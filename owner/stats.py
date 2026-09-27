"""Turn one day's log CSV into numbers. No LLM, same input gives same output.

CSV columns: time,trigger,state,confidence,why,action,bark_level,distance_cm
"""
import csv
from datetime import datetime

CALM_STATES = {"calm", "sleeping", "playing"}  # "it worked" if the next look is one of these
MAX_GAP_MIN = 10  # a look counts for at most 10 min (so a laptop nap doesn't count as "calm")


def read_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def summarize(rows):
    # 1. Share of time per state. Each look lasts until the next look.
    minutes = {}
    for i, row in enumerate(rows):
        if i + 1 < len(rows):
            gap = (_t(rows[i + 1]) - _t(row)).total_seconds() / 60
            gap = min(gap, MAX_GAP_MIN)
        else:
            gap = 5  # last look of the day: assume one normal timer cycle
        minutes[row["state"]] = minutes.get(row["state"], 0) + gap
    total = sum(minutes.values()) or 1
    state_percent = {s: round(100 * m / total) for s, m in sorted(minutes.items())}

    # 2. Anxious episodes: a run of anxious looks in a row is one episode.
    episodes = []
    for i, row in enumerate(rows):
        if row["state"] != "anxious":
            continue
        if i > 0 and rows[i - 1]["state"] == "anxious":
            episodes[-1]["looks"] += 1
            episodes[-1]["end"] = _hm(row)
        else:
            episodes.append({"start": _hm(row), "end": _hm(row), "looks": 1})

    # 3. Each calming tool (voice, ball): how often tried, how often the next look was calm.
    # Treats are skipped: they are only given once the dog is already calm (a reward),
    # so their "success rate" would always be ~100% and mislead the owner. Alerts aren't calming tools.
    interventions = {}
    treats = 0
    for i, row in enumerate(rows):
        action = row["action"]
        if action == "treat":
            treats += 1
        if action in ("none", "treat", "alert"):
            continue
        stats = interventions.setdefault(action, {"tries": 0, "worked": 0})
        stats["tries"] += 1
        if i + 1 < len(rows) and rows[i + 1]["state"] in CALM_STATES:
            stats["worked"] += 1

    return {
        "looks": len(rows),
        "first_look": _hm(rows[0]) if rows else None,
        "last_look": _hm(rows[-1]) if rows else None,
        "state_percent": state_percent,
        "anxious_episodes": episodes,
        "interventions": interventions,
        "treats_given": treats,
    }


def _t(row):
    return datetime.fromisoformat(row["time"])


def _hm(row):
    return _t(row).strftime("%H:%M")
