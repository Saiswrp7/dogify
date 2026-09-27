"""Send a Telegram message to the owner.

Use from code:     from owner.notify import send
Use from terminal: python -m owner.notify "hello"
"""
import os
import sys
from pathlib import Path

import requests

ENV_FILE = Path(__file__).parent / ".env"


def load_env():
    """Read KEY=VALUE lines from owner/.env. Real env vars win."""
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"'))


def send(text: str) -> bool:
    """Send text to the owner's Telegram. Returns True if it arrived.

    Never raises: the brain loop must keep running even if Telegram is down.
    """
    load_env()
    token = os.environ.get("DOG_BOT_TOKEN")
    chat_id = os.environ.get("DOG_CHAT_ID")
    if not token or not chat_id:
        print(f"[telegram not configured] {text}")
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
        if r.ok:
            return True
        print(f"[telegram error {r.status_code}] {r.text[:200]}")
    except requests.RequestException as e:
        print(f"[telegram failed] {e}")
    print(f"[message not sent] {text}")
    return False


if __name__ == "__main__":
    message = " ".join(sys.argv[1:]) or "Test message from the dog device."
    print("sent" if send(message) else "not sent")
