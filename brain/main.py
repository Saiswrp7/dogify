"""The brain's main loop.

  python main.py                  real box, webcam, mic and Claude. Logs to DogDevice/logs/
  python main.py --dry-run        everything fake (box, frames, Claude, audio). Logs to a temp folder
  python main.py --dry-run --fast short timers, for demos
  Stop with Ctrl+C.

Every few seconds it checks two cheap signals: mic loudness and distance to the box.
It asks Claude to look (3 webcam frames) only when:
  bark     barking stayed loud for 10 s
  near     the dog was close to the box (< 40 cm) several checks in a row
  timer    5 minutes passed since the last look
  recheck  2 minutes after we played the voice or rolled the ball
Then ladder.decide() picks the action, we do it, and one CSV row is logged.
"""
import argparse
import csv
import json
import random
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

import anthropic

import ladder
from box import PORT, Box, FakeBox
from classify import budget, classify, fake_classify
from screen import tell_screen
from sense import BARK_LOUD, SenseError, bark_level, grab_frames

ROOT = Path(__file__).resolve().parent.parent  # the DogDevice folder
sys.path.insert(0, str(ROOT))                  # lets us import owner.notify
VOICES = ROOT / "voices"
AUDIO_FILES = {".mp3", ".m4a", ".wav", ".aiff", ".aif", ".caf"}
COLUMNS = ["time", "trigger", "state", "confidence", "why", "action", "bark_level", "distance_cm"]
NEAR_CM = 40

# Timers in seconds.
NORMAL = {"tick": 5, "loud_for": 10, "near_times": 3, "look_every": 300, "min_gap": 60, "frame_gap": 5}
FAST = {"tick": 1, "loud_for": 3, "near_times": 2, "look_every": 15, "min_gap": 5, "frame_gap": 1}


def main():
    parser = argparse.ArgumentParser(description="Dog device brain loop")
    parser.add_argument("--dry-run", action="store_true", help="fake box, frames, Claude and audio")
    parser.add_argument("--fast", action="store_true", help="short timers for demos")
    parser.add_argument("--log-dir", type=Path, help="where CSV logs go")
    parser.add_argument("--port", default=PORT, help="serial port of the dog box")
    args = parser.parse_args()

    if args.log_dir is None:  # dry runs never write into the real logs folder
        args.log_dir = Path(tempfile.gettempdir()) / "dogdevice-dry-run" if args.dry_run else ROOT / "logs"
    timers = FAST if args.fast else NORMAL
    rules = ladder.FAST_RULES if args.fast else ladder.Rules()
    box = FakeBox() if args.dry_run else Box(args.port)
    history = load_history(args.log_dir)  # today's earlier looks, so the treat cap survives a restart
    print(f"Brain running{' (dry run)' if args.dry_run else ''}. Logging to {args.log_dir}. Ctrl+C to stop.")

    loud_since = None   # when the current stretch of barking started
    near_count = 0      # how many checks in a row the dog was near the box
    last_look = None    # when Claude last looked (time.monotonic seconds)
    recheck_at = None   # when to look again after voice or ball
    try:
        while True:
            now = time.monotonic()
            bark = random.choice([0.01, 0.02, 0.3]) if args.dry_run else bark_level(1)
            distance = box.distance()
            loud_since = (loud_since or now) if bark >= BARK_LOUD else None
            near_count = near_count + 1 if 0 <= distance < NEAR_CM else 0

            since_look = float("inf") if last_look is None else now - last_look
            trigger = None
            if recheck_at is not None and now >= recheck_at:
                trigger = "recheck"
            elif since_look >= timers["min_gap"] and loud_since and now - loud_since >= timers["loud_for"]:
                trigger = "bark"
            elif since_look >= timers["min_gap"] and near_count >= timers["near_times"]:
                trigger = "near"
            elif since_look >= timers["look_every"]:
                trigger = "timer"

            if trigger:
                action = look(trigger, bark, distance, args, timers, rules, box, history)
                last_look = time.monotonic()
                loud_since, near_count = None, 0
                wants_recheck = action in ("voice", "ball")
                recheck_at = last_look + rules.recheck_after.total_seconds() if wants_recheck else None
            time.sleep(timers["tick"])
    except SenseError as e:
        sys.exit(f"Stopped: {e}")
    except KeyboardInterrupt:
        print("\nStopped.")


def look(trigger, bark, distance, args, timers, rules, box, history):
    """Ask Claude (or the fake) what the dog is doing, act on it, log it. Returns the action."""
    try:
        if args.dry_run:
            result = fake_classify([], bark)
        else:
            frames = grab_frames(3, timers["frame_gap"])
            result = classify(frames, bark, timers["frame_gap"])
    except budget.BudgetExceeded as e:
        alert(f"The dog device stopped watching: {e}", args.dry_run)
        sys.exit(str(e))
    except anthropic.AuthenticationError:
        sys.exit("Claude rejected the API key (401). Export a valid ANTHROPIC_API_KEY and retry.")
    except anthropic.APIError as e:
        print(f"Claude call failed, skipping this look: {e}")
        return "none"

    now = datetime.now()
    action = ladder.decide(result["state"], history, now, rules)
    print(f"{now:%H:%M:%S} [{trigger}] {result['state']} ({result['confidence']:.0%}) "
          f"bark={bark:.2f} dist={distance} -> {action}. {result['why']}")
    act(action, result, box, args.dry_run)

    history.append({"time": now, "state": result["state"], "action": action})
    write_row(args.log_dir, {
        "time": now.isoformat(timespec="seconds"), "trigger": trigger, "state": result["state"],
        "confidence": round(result["confidence"], 2), "why": result["why"], "action": action,
        "bark_level": round(bark, 3), "distance_cm": distance,
    })
    return action


def act(action, result, box, dry_run):
    if action in ("voice", "treat", "ball"):
        tell_screen(action, result["state"])
    try:
        if action == "voice":
            play_voice(dry_run)
        elif action == "treat" and not box.treat():
            print("  box did not confirm the treat")
        elif action == "ball" and not box.ball():
            print("  box did not confirm the ball")
        elif action == "alert":
            alert(f"Your dog still looks {result['state']} after the voice and the ball. "
                  f"Claude saw: {result['why']}", dry_run)
    except Exception as e:  # a failed action should not stop the whole loop
        print(f"  {action} failed: {e}")


def play_voice(dry_run):
    clips = [p for p in VOICES.glob("*") if p.suffix.lower() in AUDIO_FILES]
    if not clips:
        print("  no voice clips in voices/ yet, skipping the voice")
        return
    clip = random.choice(clips)
    if dry_run:
        print(f"  (dry run) would play {clip.name}")
        return
    subprocess.run(["afplay", str(clip)])


def alert(text, dry_run):
    if dry_run:
        print(f"  (dry run) would alert the owner: {text}")
        return
    try:
        from owner.notify import send
        send(text)
    except Exception as e:
        print(f"  ALERT (could not send: {e}): {text}")


def write_row(log_dir, row):
    """Append one row to logs/YYYY-MM-DD.csv, writing the header if the file is new."""
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"{row['time'][:10]}.csv"
    is_new = not path.exists()
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if is_new:
            writer.writeheader()
        writer.writerow(row)


def load_history(log_dir):
    path = log_dir / f"{datetime.now():%Y-%m-%d}.csv"
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return [{"time": datetime.fromisoformat(r["time"]), "state": r["state"], "action": r["action"]}
                for r in csv.DictReader(f)]


if __name__ == "__main__":
    main()
