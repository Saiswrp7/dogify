"""The owner's remote control on Telegram.

Run from DogDevice/:  .venv/bin/python -m owner.ask_bot   (leave it running)
Buttons under the chat:
  🐶 What's he doing?  -> photo now + Claude's read + today's summary (~$0.003, counts toward the $20 cap)
  🔊 Voice / 🦴 Treat / 🎾 Ball -> the device does it right away, the dog screen shows it,
                                    and it is logged (trigger "owner") so the daily report counts it.
  🎤 voice note (hold the mic)  -> plays right away to the dog, and joins the brain's calming voices
  📹 Play my video             -> plays the last video the owner sent (video or round video message)
                                    full screen with sound on the dog screen.
Any other text is treated as "what's he doing?". Messages from other chats are ignored.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "brain"))  # reuse the brain's camera, mic and Claude code

from budget import BudgetExceeded           # noqa: E402
from box import Box                         # noqa: E402
from classify import classify               # noqa: E402
from main import play_voice, write_row      # noqa: E402
from screen import tell_screen              # noqa: E402
from sense import SenseError, bark_level, grab_frames  # noqa: E402

from owner.notify import load_env           # noqa: E402
from owner.stats import read_rows, summarize  # noqa: E402

FRIENDLY = {"calm": "calm and relaxed", "anxious": "anxious", "lonely": "a bit lonely",
            "sleeping": "sleeping", "playing": "playing", "not_visible": "not in view of the camera"}


LOGS = ROOT / "logs"
OWNER_VIDEO = ROOT / "dogscreen" / "owner_video.mp4"
BUTTONS = {"keyboard": [["🐶 What's he doing?"], ["🔊 Voice", "🦴 Treat", "🎾 Ball"], ["📹 Play my video"]],
           "resize_keyboard": True, "is_persistent": True}


def api(method, **kwargs):
    token = os.environ["DOG_BOT_TOKEN"]
    r = requests.post(f"https://api.telegram.org/bot{token}/{method}", timeout=40, **kwargs)
    r.raise_for_status()
    return r.json()["result"]


def today_summary(dog):
    path = LOGS / f"{date.today().isoformat()}.csv"
    rows = read_rows(path) if path.exists() else []
    if not rows:
        return "No log for today yet, so this is the first look."
    s = summarize(rows)
    lines = [f"Today since {s['first_look']}: calm or asleep "
             f"{s['state_percent'].get('calm', 0) + s['state_percent'].get('sleeping', 0)}% of the time."]
    eps = s["anxious_episodes"]
    lines.append(f"{len(eps)} anxious moment(s)" + (f", last at {eps[-1]['start']}." if eps else "."))
    for action, t in s["interventions"].items():
        lines.append(f"{action.capitalize()} calmed {dog} {t['worked']} of {t['tries']} times.")
    if s["treats_given"]:
        lines.append(f"Treats earned: {s['treats_given']}.")
    return "\n".join(lines)


def how_far(dog, state):
    """Ultrasonic reading turned into words. The sensor sees the nearest thing straight in front
    of the box, which may be a wall, so we only call it the dog when it's close and the camera sees him."""
    try:
        cm = Box().distance()
    except Exception:
        return "Box sensor not connected."
    seen = state not in ("not_visible",)
    if cm < 0:
        return "Nothing in front of the box right now."
    if cm <= 40:
        return f"{'He is' if seen else 'Something is'} right at the box ({cm} cm)."
    if cm <= 150:
        return f"{'He is probably' if seen else 'Something is'} about {cm} cm from the box."
    return f"Not near the box (nearest thing in front of it is {cm} cm away)."


QUESTION_START = ("what", "how", "is ", "are ", "show", "where", "check", "see", "can i see")
COMMANDS = [("video", ("video", "clip")),
            ("voice", ("voice", "talk", "speak", "calm", "my message")),
            ("treat", ("treat", "snack", "biscuit", "food", "reward")),
            ("ball",  ("ball", "roll", "play"))]


def route(text):
    """Turn what the owner typed (or a button) into check / voice / treat / ball / video / help."""
    t = text.lower().strip()
    if t in ("/start", "/help", "help"):
        return "help"
    if t.endswith("?") or t.startswith(QUESTION_START):
        return "check"  # "what is my dog doing?", "show me my dog", "is he calm?"
    for action, words in COMMANDS:
        if any(w in t for w in words):
            return action
    return "check"


def say(chat_id, text):
    api("sendMessage", json={"chat_id": chat_id, "text": text, "reply_markup": BUTTONS})


def last_state():
    path = LOGS / f"{date.today().isoformat()}.csv"
    rows = read_rows(path) if path.exists() else []
    return rows[-1]["state"] if rows else "not_visible"


VOICES = ROOT / "voices"
KEEP_VOICE_NOTES = 5


def download(file_id):
    info = api("getFile", json={"file_id": file_id})
    r = requests.get(f"https://api.telegram.org/file/bot{os.environ['DOG_BOT_TOKEN']}/{info['file_path']}", timeout=60)
    r.raise_for_status()
    return r.content


def play_voice_note(chat_id, dog, msg):
    """The owner sent a voice note: play it to the dog now, and keep it for the brain's calming voices."""
    media = msg.get("voice") or msg.get("audio")
    raw = VOICES / "tg_incoming.oga"
    raw.write_bytes(download(media["file_id"]))
    clip = VOICES / f"tg_{datetime.now():%Y%m%d_%H%M%S}.m4a"
    ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"  # afplay can't play Telegram's opus
    subprocess.run([ffmpeg, "-loglevel", "error", "-y", "-i", str(raw), "-c:a", "aac", "-b:a", "96k", str(clip)], check=True)
    raw.unlink()
    for old in sorted(VOICES.glob("tg_*.m4a"))[:-KEEP_VOICE_NOTES]:
        old.unlink()

    state = last_state()
    tell_screen("voice", state)
    say(chat_id, f"Playing your voice note to {dog} now.")
    subprocess.run(["afplay", str(clip)])
    write_row(LOGS, {"time": datetime.now().isoformat(timespec="seconds"), "trigger": "owner",
                     "state": state, "confidence": 0, "why": "owner sent a voice note on Telegram",
                     "action": "voice", "bark_level": 0, "distance_cm": -1})
    say(chat_id, f"Done. I also added it to {dog}'s calming voices (the {KEEP_VOICE_NOTES} newest voice notes are kept).")


def save_video(chat_id, dog, msg):
    """The owner sent a video or a round video message: keep it for the dog screen."""
    media = msg.get("video_note") or msg.get("video")
    info = api("getFile", json={"file_id": media["file_id"]})
    r = requests.get(f"https://api.telegram.org/file/bot{os.environ['DOG_BOT_TOKEN']}/{info['file_path']}", timeout=60)
    r.raise_for_status()
    tmp = OWNER_VIDEO.with_suffix(".tmp")
    tmp.write_bytes(r.content)
    tmp.replace(OWNER_VIDEO)
    say(chat_id, f"Saved your video ({len(r.content) // 1024} KB). Tap 📹 Play my video to show it to {dog}.")


def owner_action(chat_id, dog, action):
    """The owner pressed Voice, Treat, Ball or Play my video."""
    if action == "video" and not OWNER_VIDEO.exists():
        return say(chat_id, "Send me a video first: hold the round camera button in this chat and talk to him.")
    state = last_state()
    tell_screen(action, state)
    try:
        if action == "video":
            done = True
            say(chat_id, f"Playing your video on {dog}'s screen now.")
        elif action == "voice":
            say(chat_id, f"Playing your voice for {dog} now.")
            play_voice(dry_run=False)
            done = True
        else:
            box = Box()
            done = box.treat() if action == "treat" else box.ball()
    except Exception as e:
        return say(chat_id, f"The box didn't respond ({e}). Is it plugged in?")
    write_row(LOGS, {"time": datetime.now().isoformat(timespec="seconds"), "trigger": "owner",
                     "state": state, "confidence": 0, "why": f"owner pressed {action} on Telegram",
                     "action": action, "bark_level": 0, "distance_cm": -1})
    if action == "treat":
        tip = (" Tip: treats work best once he's calm, so he doesn't learn that barking gets snacks."
               if state == "anxious" else "")
        say(chat_id, ("Treat dropped." if done else "Sent the treat, but the box didn't confirm.") + tip)
    elif action == "ball":
        say(chat_id, "Ball rolled out." if done else "Sent the ball, but the box didn't confirm.")


def answer(chat_id, dog):
    api("sendChatAction", json={"chat_id": chat_id, "action": "upload_photo"})
    try:
        bark = bark_level(1)
        frames = grab_frames(2, gap_s=2)
        result = classify(frames, bark, gap_s=2)
    except BudgetExceeded as e:
        return api("sendMessage", json={"chat_id": chat_id, "text": f"Can't check right now: {e}"})
    except SenseError as e:
        return api("sendMessage", json={"chat_id": chat_id, "text": f"Camera or mic problem: {e}"})
    except Exception as e:
        return api("sendMessage", json={"chat_id": chat_id, "text": f"Couldn't check just now ({e}). Try again in a minute."})

    caption = (f"{dog} looks {FRIENDLY.get(result['state'], result['state'])} right now "
               f"({round(result['confidence'] * 100)}% sure).\n{result['why']}\n"
               f"📏 {how_far(dog, result['state'])}\n\n{today_summary(dog)}")
    api("sendPhoto", data={"chat_id": chat_id, "caption": caption[:1024],
                           "reply_markup": json.dumps(BUTTONS)},
        files={"photo": ("dog.jpg", frames[-1], "image/jpeg")})
    print(f"{time.strftime('%H:%M:%S')} answered: {result['state']}")


def main():
    load_env()
    owner = os.environ.get("DOG_CHAT_ID")
    dog = os.environ.get("DOG_NAME", "your dog")
    if not os.environ.get("DOG_BOT_TOKEN") or not owner:
        sys.exit("Set DOG_BOT_TOKEN and DOG_CHAT_ID in owner/.env first (see owner/SETUP.md).")

    # Skip messages sent while the bot was off, so it doesn't answer a pile of old questions.
    old = api("getUpdates", json={"offset": -1})
    offset = old[-1]["update_id"] + 1 if old else None
    print(f"Listening. Ask the bot anything on Telegram and it checks on {dog}. Ctrl+C to stop.")
    say(owner, f"The dog device is on. Tap a button below to check on {dog} or help him.")

    while True:
        try:
            updates = api("getUpdates", json={"offset": offset, "timeout": 30})
        except requests.RequestException as e:
            print(f"telegram unreachable ({e}), retrying in 10 s")
            time.sleep(10)
            continue
        for u in updates:
            offset = u["update_id"] + 1
            msg = u.get("message") or {}
            if str(msg.get("chat", {}).get("id")) != owner:
                continue  # private bot: only the owner gets answers
            text = msg.get("text", "")
            if msg.get("voice") or msg.get("audio"):
                try:
                    play_voice_note(owner, dog, msg)
                except Exception as e:
                    say(owner, f"Couldn't play that voice note ({e}).")
            elif msg.get("video_note") or msg.get("video"):
                try:
                    save_video(owner, dog, msg)
                except Exception as e:
                    say(owner, f"Couldn't save that video ({e}). Try a shorter one (under 20 MB).")
            elif route(text) == "help":
                say(owner, f"Tap a button or just type: \"show me my dog\", \"calm voice\", \"give treat\", "
                           "\"roll the ball\", \"play my video\". Send a voice note and I'll play it to him right away, "
                           "or a video message to show on his screen.")
            elif route(text) == "check":
                answer(owner, dog)
            else:
                owner_action(owner, dog, route(text))


if __name__ == "__main__":
    main()
