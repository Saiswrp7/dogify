"""Daily report for the owner.

python -m owner.report                 today's report, printed
python -m owner.report 2026-09-27      a given day
python -m owner.report --send          send it to Telegram
python -m owner.report --no-llm        simple report without Claude
"""
import argparse
import json
import os
from datetime import date
from pathlib import Path

import anthropic

import budget
from owner.notify import load_env, send
from owner.stats import read_rows, summarize

LOGS_DIR = Path(__file__).parent.parent / "logs"
MODEL = "claude-sonnet-5"

SYSTEM = """You write a short daily report for a dog owner about how their dog did while they were away.
Warm, calm, plain text for a phone. No markdown, no tables, no em dashes, no bullet symbols.
About 6 to 10 short lines. Cover: how the mood moved through the day, the anxious episodes,
what worked and what didn't (like "your voice calmed Bruno 3 of 4 times"), and end with one
concrete suggestion. Use only the numbers in STATS. Never invent or recompute numbers.
If there is little data, say so honestly.
Treats are a reward the device gives only after the dog has calmed down, never a calming tool.
Report how many treats were earned, but never suggest giving treats while the dog is anxious or barking:
that teaches the dog that barking gets treats. Suggestions should be about voice, the ball, or the owner's routine."""


def plain_report(stats, dog):
    """Fallback report built only from the numbers. No API call."""
    lines = [f"{dog}'s day ({stats['first_look']} to {stats['last_look']}, {stats['looks']} looks)"]
    lines.append("Time spent: " + ", ".join(f"{s} {p}%" for s, p in stats["state_percent"].items()))
    eps = stats["anxious_episodes"]
    if eps:
        starts = ", ".join(e["start"] for e in eps)
        lines.append(f"Anxious episodes: {len(eps)} (started at {starts})")
    else:
        lines.append("No anxious episodes today.")
    for action, s in stats["interventions"].items():
        lines.append(f"{action}: calmed {dog} {s['worked']} of {s['tries']} times")
    lines.append(f"Treats given: {stats['treats_given']}")
    return "\n".join(lines)


def claude_report(stats, csv_text, dog):
    budget.check()
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": "medium"},
        system=SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Dog's name: {dog}\n\nSTATS (already computed, trust these):\n"
                       f"{json.dumps(stats, indent=2)}\n\nRAW LOG CSV:\n{csv_text}",
        }],
    )
    budget.record(MODEL, response.usage)
    if response.stop_reason == "refusal":
        raise RuntimeError("Claude declined to write the report")
    return "".join(b.text for b in response.content if b.type == "text").strip()


def main():
    parser = argparse.ArgumentParser(description="Daily dog report")
    parser.add_argument("day", nargs="?", default=date.today().isoformat(), help="YYYY-MM-DD")
    parser.add_argument("--send", action="store_true", help="send to Telegram instead of printing")
    parser.add_argument("--no-llm", action="store_true", help="plain report, no Claude call")
    parser.add_argument("--logs", default=LOGS_DIR, type=Path, help="folder with the CSV logs")
    args = parser.parse_args()

    load_env()
    dog = os.environ.get("DOG_NAME", "your dog")
    path = args.logs / f"{args.day}.csv"
    if not path.exists():
        text = f"No log for {args.day} yet ({path})."
    else:
        rows = read_rows(path)
        stats = summarize(rows)
        if not rows:
            text = f"The log for {args.day} is empty."
        elif args.no_llm:
            text = plain_report(stats, dog)
        else:
            try:
                text = claude_report(stats, path.read_text(), dog)
            except (anthropic.APIError, RuntimeError, TypeError) as e:
                # Bad key, no internet, refusal: still give the owner the numbers.
                # (The SDK raises TypeError when no API key is set at all.)
                print(f"[claude failed, using plain report] {e}")
                text = plain_report(stats, dog)

    if args.send:
        send(text)
    else:
        print(text)


if __name__ == "__main__":
    main()
