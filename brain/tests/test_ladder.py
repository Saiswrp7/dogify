"""Tests for the escalation ladder. Run from the brain folder:  pytest

The ladder never reads the real clock, so each test builds its own fake times.
"""
from datetime import datetime, timedelta

from ladder import Rules, decide

START = datetime(2026, 9, 27, 10, 0, 0)
RULES = Rules()


def at(minutes):
    return START + timedelta(minutes=minutes)


def look(minutes, state, action):
    return {"time": at(minutes), "state": state, "action": action}


def test_ok_states_do_nothing():
    for state in ["calm", "sleeping", "playing", "not_visible"]:
        assert decide(state, [], at(0)) == "none"


def test_anxious_escalates_voice_ball_alert():
    history = []
    for minute, expected in [(0, "voice"), (2, "ball"), (4, "alert"), (6, "none")]:
        action = decide("anxious", history, at(minute))
        assert action == expected
        history.append(look(minute, "anxious", action))


def test_calm_after_help_gets_a_treat():
    history = [look(0, "anxious", "voice")]
    assert decide("calm", history, at(2)) == "treat"


def test_calm_without_help_gets_no_treat():
    assert decide("calm", [look(0, "calm", "none")], at(5)) == "none"


def test_never_treat_while_anxious():
    histories = [[], [look(0, "anxious", "voice")], [look(0, "anxious", "voice"), look(2, "anxious", "ball")]]
    for history in histories:
        assert decide("anxious", history, at(3)) != "treat"


def test_only_one_treat_per_calm_episode():
    history = [look(0, "anxious", "voice"), look(2, "calm", "treat")]
    assert decide("calm", history, at(30)) == "none"


def test_treat_gap_20_minutes():
    history = [look(0, "anxious", "voice"), look(2, "calm", "treat"), look(15, "anxious", "voice")]
    assert decide("calm", history, at(17)) == "none"   # only 15 min since the last treat
    assert decide("calm", history, at(22)) == "treat"  # 20 min since the last treat


def test_daily_treat_cap():
    history = []
    for i in range(RULES.daily_treats):  # 6 treats today, 30 min apart
        history += [look(i * 30, "anxious", "voice"), look(i * 30 + 2, "calm", "treat")]
    history.append(look(300, "anxious", "voice"))
    assert decide("calm", history, at(302)) == "none"
    tomorrow = START + timedelta(days=1)
    history.append({"time": tomorrow, "state": "anxious", "action": "voice"})
    assert decide("calm", history, tomorrow + timedelta(minutes=2)) == "treat"


def test_same_action_not_repeated_within_5_minutes():
    history = [look(0, "anxious", "voice"), look(2, "calm", "treat")]
    assert decide("anxious", history, at(3)) == "none"   # voice played 3 min ago
    assert decide("anxious", history, at(5)) == "voice"  # 5 min later it's allowed again


def test_old_help_is_forgotten():
    history = [look(0, "anxious", "voice")]
    assert decide("anxious", history, at(20)) == "voice"  # starts over instead of jumping to ball


def test_lonely_gets_voice_then_ball_then_nothing():
    history = []
    for minute, expected in [(0, "voice"), (2, "ball"), (4, "none")]:
        action = decide("lonely", history, at(minute))
        assert action == expected
        history.append(look(minute, "lonely", action))


def test_not_visible_does_not_break_the_ladder():
    history = [look(0, "anxious", "voice"), look(2, "not_visible", "none")]
    assert decide("anxious", history, at(4)) == "ball"
