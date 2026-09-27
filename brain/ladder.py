"""The escalation ladder: what to do, given what Claude sees now and what we did before.

decide() is a pure function: no clock, no hardware, no files inside. Same inputs, same answer.
That makes it easy to test (see tests/test_ladder.py).

The rules (from the README):
  calm / sleeping / playing      -> nothing
  anxious                        -> voice, look again in 2 min
  still anxious after the voice  -> roll the ball
  still anxious after the ball   -> alert the owner
  lonely                         -> voice, then ball
  calm again after any help      -> treat (we reward calm, never barking)
  At most 1 treat per 20 min, at most 6 per day, and the same action at most once per 5 min.
"""
from dataclasses import dataclass
from datetime import timedelta

OK_STATES = {"calm", "sleeping", "playing"}
HELP_ACTIONS = {"voice", "ball", "alert"}
ACTIONS = ["none", "voice", "treat", "ball", "alert"]


@dataclass
class Rules:
    recheck_after: timedelta = timedelta(minutes=2)  # look again this long after voice or ball
    treat_gap: timedelta = timedelta(minutes=20)     # at most 1 treat per this long
    daily_treats: int = 6                            # at most this many treats per day
    repeat_gap: timedelta = timedelta(minutes=5)     # the same voice/ball/alert at most once per this long
    episode: timedelta = timedelta(minutes=15)       # help older than this is forgotten; the ladder starts over


# Short timers for demos (main.py --fast).
FAST_RULES = Rules(recheck_after=timedelta(seconds=10), treat_gap=timedelta(seconds=30),
                   repeat_gap=timedelta(seconds=8), episode=timedelta(seconds=60))


def decide(state, history, now, rules=Rules()):
    """Pick the next action.

    state:   what Claude sees right now, e.g. "anxious"
    history: earlier looks, oldest first. Each is a dict with "time" (datetime), "state" and "action".
    now:     the current time (datetime)
    Returns one of ACTIONS.
    """
    helps = [h["action"] for h in current_episode(history, now, rules) if h["action"] in HELP_ACTIONS]
    last_help = helps[-1] if helps else None

    if state in OK_STATES:
        if state == "calm" and last_help and treat_allowed(history, now, rules):
            return "treat"  # the dog calmed down after we helped: reward that
        return "none"

    if state == "anxious":
        want = {None: "voice", "voice": "ball", "ball": "alert"}.get(last_help, "none")
    elif state == "lonely":
        want = {None: "voice", "voice": "ball"}.get(last_help, "none")
    else:  # not_visible, or anything unexpected
        return "none"

    if want != "none" and done_recently(want, history, now, rules.repeat_gap):
        return "none"
    return want


def current_episode(history, now, rules):
    """The looks since the dog was last seen OK, ignoring anything older than rules.episode."""
    episode = []
    for h in history:
        if h["state"] in OK_STATES:
            episode = []  # an OK look ends the episode
        elif now - h["time"] <= rules.episode:
            episode.append(h)
    return episode


def treat_allowed(history, now, rules):
    treats = [h["time"] for h in history if h["action"] == "treat"]
    treats_today = [t for t in treats if t.date() == now.date()]
    if len(treats_today) >= rules.daily_treats:
        return False
    return not treats or now - treats[-1] >= rules.treat_gap


def done_recently(action, history, now, gap):
    return any(h["action"] == action and now - h["time"] < gap for h in history)
