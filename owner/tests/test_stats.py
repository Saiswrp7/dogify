"""Tests for owner/stats.py. They only use tmp_path, never DogDevice/logs/."""
from owner.stats import read_rows, summarize

HEADER = "time,trigger,state,confidence,why,action,bark_level,distance_cm\n"


def write_csv(tmp_path, lines):
    path = tmp_path / "day.csv"
    path.write_text(HEADER + "\n".join(lines) + "\n")
    return read_rows(path)


def test_episodes_and_interventions(tmp_path):
    rows = write_csv(tmp_path, [
        "2026-09-27T10:00:00,timer,calm,0.9,lying down,none,10,120",
        "2026-09-27T10:05:00,bark,anxious,0.8,barking at door,voice,70,90",
        "2026-09-27T10:07:00,recheck,calm,0.8,settled,treat,15,30",   # voice worked
        "2026-09-27T10:09:00,recheck,calm,0.9,eating,none,5,25",      # treat worked
        "2026-09-27T10:30:00,bark,anxious,0.8,pacing,voice,65,100",
        "2026-09-27T10:32:00,recheck,anxious,0.7,still pacing,ball,60,100",  # voice failed
        "2026-09-27T10:34:00,recheck,playing,0.8,chasing ball,none,20,80",   # ball worked
    ])
    s = summarize(rows)

    assert s["looks"] == 7
    assert s["anxious_episodes"] == [
        {"start": "10:05", "end": "10:05", "looks": 1},
        {"start": "10:30", "end": "10:32", "looks": 2},
    ]
    assert s["interventions"] == {
        "voice": {"tries": 2, "worked": 1},
        "ball": {"tries": 1, "worked": 1},
    }
    assert s["treats_given"] == 1


def test_state_percent_is_time_weighted_and_capped(tmp_path):
    rows = write_csv(tmp_path, [
        "2026-09-27T09:00:00,timer,sleeping,0.9,asleep,none,0,150",   # 3 hour gap, capped at 10 min
        "2026-09-27T12:00:00,timer,anxious,0.8,whining,none,40,100",  # last row counts 5 min
    ])
    s = summarize(rows)
    assert s["state_percent"] == {"anxious": 33, "sleeping": 67}
    assert s["anxious_episodes"] == [{"start": "12:00", "end": "12:00", "looks": 1}]
    assert s["interventions"] == {}


def test_last_row_action_counts_as_tried_not_worked(tmp_path):
    rows = write_csv(tmp_path, [
        "2026-09-27T20:00:00,bark,anxious,0.8,barking,voice,70,90",
    ])
    s = summarize(rows)
    assert s["interventions"] == {"voice": {"tries": 1, "worked": 0}}
    assert s["treats_given"] == 0


def test_empty_log(tmp_path):
    s = summarize(write_csv(tmp_path, []))
    assert s["looks"] == 0
    assert s["anxious_episodes"] == []
