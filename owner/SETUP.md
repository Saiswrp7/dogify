# Owner side setup

Run every command from the `DogDevice/` folder.

## 1. Make a Telegram bot (2 minutes)
1. In Telegram, open a chat with **@BotFather**.
2. Send `/newbot`. Pick a name (like "Bruno Watch") and a username ending in `bot`.
3. BotFather replies with a **token** like `123456:ABC...`. Keep it secret.

## 2. Save the token
Create the file `owner/.env` with this line (it is git-ignored):
```
DOG_BOT_TOKEN=123456:ABC...
DOG_NAME=Bruno
```

## 3. Find your chat id
1. In Telegram, open your new bot and send it any message, like "hi".
2. Run:
```
.venv/bin/python -m owner.get_chat_id
```
3. It prints `DOG_CHAT_ID=...`. Add that line to `owner/.env`.

## 4. Test it
```
.venv/bin/python -m owner.notify "hello"
```
Your phone should buzz. If it prints `[telegram not configured]`, check `owner/.env`.

## 5. Daily report
```
.venv/bin/python -m owner.report --no-llm           # numbers only, no Claude
.venv/bin/python -m owner.report                    # Claude writes it (needs ANTHROPIC_API_KEY)
.venv/bin/python -m owner.report --send             # send it to your phone
.venv/bin/python -m owner.report 2026-09-26         # a different day
```

## 6. Send it every night at 9 PM (optional)
Run `crontab -e` and add this line (fix the path if yours differs):
```
0 21 * * * cd "$HOME/Desktop/Claude Folders/DogDevice" && .venv/bin/python -m owner.report --send
```
Cron does not see your shell's exported variables, so put `ANTHROPIC_API_KEY=...` in `owner/.env` too.

## Run the tests
```
.venv/bin/python -m pytest owner/tests
```
