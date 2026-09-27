"""Print your Telegram chat id.

1. Put DOG_BOT_TOKEN in owner/.env
2. Send any message to your new bot in Telegram
3. Run: python -m owner.get_chat_id
"""
import os

import requests

from owner.notify import load_env

load_env()
token = os.environ.get("DOG_BOT_TOKEN")
if not token:
    raise SystemExit("DOG_BOT_TOKEN is not set. Put it in owner/.env first.")

r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)
data = r.json()
if not data.get("ok"):
    raise SystemExit(f"Telegram said no: {data}")

chats = {}
for update in data["result"]:
    msg = update.get("message") or update.get("edited_message")
    if msg:
        chat = msg["chat"]
        chats[chat["id"]] = chat.get("first_name") or chat.get("title") or ""

if not chats:
    print("No messages yet. Send your bot a message in Telegram, then run this again.")
for chat_id, name in chats.items():
    print(f"DOG_CHAT_ID={chat_id}   ({name})")
