"""Tell the dog screen (dogscreen/index.html) what just happened."""
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def tell_screen(action, state):
    """Tell the dog screen (dogscreen/index.html) what just happened. Written before acting,
    so the owner's face is on screen while the voice plays."""
    path = ROOT / "dogscreen" / "now.json"
    old = json.loads(path.read_text()) if path.exists() else {"id": 0}
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"id": old["id"] + 1, "action": action, "state": state, "at": time.time()}))
    tmp.replace(path)  # atomic, so the page never reads half a file
