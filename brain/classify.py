"""Ask Claude what state the dog is in, from a few webcam frames plus the mic loudness.

classify() returns a dict like:
  {"state": "anxious", "confidence": 0.8, "why": "Dog is pacing by the door in all 3 frames."}
"""
import base64
import json
import os
import random
from pathlib import Path

import sys

import anthropic

from sense import BARK_LOUD

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # the DogDevice folder
import budget

MODEL = "claude-haiku-4-5-20251001"
STATES = ["calm", "anxious", "lonely", "sleeping", "playing", "not_visible"]

SYSTEM = """You watch a dog that is home alone, through a webcam. Classify the dog's state as exactly one of:
- calm: awake and relaxed, lying or sitting quietly, soft body
- anxious: pacing, panting, barking or whining, scratching at the door, trembling, ears pinned back, tail tucked, chewing furniture
- lonely: awake but low energy, waiting by the door or window, looking around for someone, not frantic
- sleeping: lying still with eyes closed
- playing: chasing or chewing a toy, play bow, bouncy loose movement
- not_visible: no dog in the frames, or too dark or blurry to tell
When there are several frames, they are a few seconds apart, oldest first: compare them to tell pacing from resting.
confidence is 0 to 1. why is one short sentence about what you actually see."""

# Structured output: Claude must answer with JSON that matches this schema.
SCHEMA = {
    "type": "object",
    "properties": {
        "state": {"type": "string", "enum": STATES},
        "confidence": {"type": "number"},
        "why": {"type": "string"},
    },
    "required": ["state", "confidence", "why"],
    "additionalProperties": False,
}

_client = None


def load_key():
    """Use ANTHROPIC_API_KEY from owner/.env if it isn't already exported."""
    env = Path(__file__).parent.parent / "owner" / ".env"
    if "ANTHROPIC_API_KEY" in os.environ or not env.exists():
        return
    for line in env.read_text().splitlines():
        if line.startswith("ANTHROPIC_API_KEY="):
            os.environ["ANTHROPIC_API_KEY"] = line.split("=", 1)[1].strip().strip('"')


def classify(frames, bark=None, gap_s=5):
    """frames: list of JPEG bytes. bark: mic loudness 0-1, or None if unknown."""
    global _client
    if _client is None:
        load_key()
        _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

    content = [{"type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg",
                           "data": base64.standard_b64encode(f).decode()}}
               for f in frames]
    if len(frames) > 1:
        text = f"These are {len(frames)} frames taken {gap_s} seconds apart, oldest first."
    else:
        text = "This is a single frame."
    if bark is None:
        text += " There is no microphone reading."
    else:
        text += (f" Microphone loudness while these were taken: {bark:.2f} "
                 f"(0 = silent; {BARK_LOUD} or more usually means barking).")
    content.append({"type": "text", "text": text})

    budget.check()
    try:
        response = _client.messages.create(
            model=MODEL,
            max_tokens=300,
            system=SYSTEM,
            messages=[{"role": "user", "content": content}],
            output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
        )
    except TypeError as e:  # the SDK raises this when no API key is set at all
        if "authentication" in str(e):
            raise SystemExit("No Anthropic API key found. Run: export ANTHROPIC_API_KEY=your-key") from e
        raise
    budget.record(MODEL, response.usage)
    if response.stop_reason == "refusal":
        return {"state": "not_visible", "confidence": 0.0, "why": "Claude declined to classify these frames."}
    text = next(block.text for block in response.content if block.type == "text")
    result = json.loads(text)
    result["confidence"] = min(max(float(result["confidence"]), 0.0), 1.0)
    return result


def fake_classify(frames, bark=None, gap_s=5):
    """A stand-in for Claude, used by --dry-run. Random, but a loud bark makes 'anxious' likely."""
    if bark is not None and bark >= BARK_LOUD:
        state = random.choice(["anxious", "anxious", "anxious", "lonely"])
    else:
        state = random.choice(["calm", "calm", "sleeping", "playing", "anxious", "lonely", "not_visible"])
    return {"state": state, "confidence": round(random.uniform(0.5, 0.95), 2), "why": "fake result (dry run)"}
