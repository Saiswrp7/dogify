# Dog Device MVP

A device that watches a dog while the owner is away, calms it when it gets anxious or lonely, and sends the owner a daily report.

- **Dog side:** detects anxiety, calmness and loneliness, then steps in with the owner's voice, a treat, or a rolling ball.
- **Owner side:** a daily report on the phone.
- **Brain:** Claude API reads camera snapshots and writes the report.

Team: 3 people.

---

## Key design decisions

1. **The camera reads behavior, not the ultrasonic sensor.** The ultrasonic only measures distance. It has two jobs: detect that the dog came close to the device, and confirm the dog came over to take a treat.
2. **Don't send every frame to Claude.** Cheap local signals decide when to ask Claude: mic loudness (barking), ultrasonic distance, and a timer every 5 minutes.
3. **Treats reward calm, not barking.** A treat given during barking teaches the dog to bark. The escalation ladder:
   - Dog anxious → play the owner's voice → wait 2 min → check again
   - Dog calmed down → treat (rewards calm)
   - Dog still anxious or lonely → roll the ball (distraction or play)
   - Cooldowns: at most 1 treat every 20 min, plus a daily cap
4. **Our edge is learning what works for each dog.** Log every intervention and whether the dog's state changed after it. The report says things like "Voice calmed Bruno 3 of 4 times, the ball 0 of 2."

---

## Architecture

```
Laptop (the brain)
 ├─ webcam → snapshot every 5 min or when triggered
 ├─ mic → bark loudness
 ├─ speaker → plays owner voice clips
 ├─ Python loop → Claude (Haiku 4.5 for frames) → JSON state → CSV log
 └─ HTTP calls → ESP32 (/treat, /ball, /distance)

ESP32 (Glyph C6, on WiFi)
 ├─ HC-SR04 ultrasonic
 ├─ servo 1 → cardboard treat disc
 └─ servo 2 → ball gate on a cardboard ramp

Owner's phone
 └─ daily report + live alerts (Telegram bot or a simple web page)
```

**Smallest possible MVP:** laptop + webcam + Claude + recorded owner voice + daily report. No hardware needed. Add the treat once that works. Add the ball last, or drop it.

**Parts to buy:** 2x SG90 servo, jumper wires. Nothing we have can move without them.

---

## Build steps

| # | Step | Done when |
|---|---|---|
| 1 | **Test the riskiest part first.** Record 20 min of a dog left alone (or use YouTube clips of dogs with separation anxiety). Send one frame every 30 s to Claude, label the same frames by hand, compare. | Claude matches our labels on 70% or more |
| 2 | **Laptop loop:** OpenCV webcam capture, mic loudness, Claude call, CSV log (time, state, trigger, action, state after). | States are logged every cycle |
| 3 | **Escalation ladder** in code, with cooldowns. | The right action fires for each state |
| 4 | **Treat dispenser:** toilet-paper roll of kibble over a cardboard disc with one hole; the servo turns the disc to line the hole up with the chute. ESP32 serves `/treat`. | Drops exactly 1 treat at least 8 times out of 10 |
| 5 | **Ultrasonic:** mounted facing the chute. | Distance under ~40 cm within 30 s of a treat logs "treat taken" |
| 6 | **Ball:** cardboard ramp, servo arm as a gate. Works once, then a person puts the ball back. | Ball rolls out on `/ball` |
| 7 | **Daily report:** send the CSV to Sonnet 5 for mood across the day, anxiety episodes, what worked, one suggestion. Deliver it to the owner's phone. | Owner gets a readable report |
| 8 | **Real dog test** for one afternoon. One of us watches and compares against Claude's labels. Get the dog used to the servo noise first. | Labels mostly match; dog isn't scared of the device |

Suggested prompt for step 1:

> Classify this dog: calm / anxious / lonely / sleeping / playing / not visible. Return JSON with state, confidence, and what you see.

A single snapshot misses pacing and whining. Consider sending 3 frames taken 5 s apart, plus the bark loudness as text.

---

## Team split

| Person | Owns | Done when |
|---|---|---|
| A: Hardware | ESP32, servos, ultrasonic, cardboard dispenser and ramp | `curl <esp32-ip>/treat` drops one treat reliably |
| B: Brain | Step 1 test, laptop loop, Claude prompts, ladder rules | Correct state is logged, right action fires |
| C: Owner side | Recording owner voice clips, report prompt, phone delivery, finding a test dog | Owner gets a readable report after the real dog test |

B's step 1 decides whether the idea works at all, so start it on day 1.

---

## Board setup (done 2026-09-27)

**Board:** PCB Cupid **Glyph C6** (ESP32-C6, 4 MB flash, WiFi 6, BLE 5). Docs: https://learn.pcbcupid.com/documentation/modules/glyph/glyph-esp32c6/overview-glyph-c6

**Status:** test sketch `hello_c6/` uploaded and running. It prints `tick` every second over USB and blinks the onboard LED.

### Arduino IDE settings
- Board package: **esp32 by Espressif Systems**, version 3.3.12. Not "Arduino ESP32 Boards", which only covers the Nano ESP32.
- Board: **Pcbcupid GLYPH C6**
- Port: **/dev/cu.usbmodem101**
- USB CDC On Boot: **Enabled** (without it the Serial Monitor stays blank)

### Uploading from the terminal
```bash
CLI="/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli"
FQBN="esp32:esp32:Pcbcupid_GLYPH_C6:CDCOnBoot=cdc"
"$CLI" compile --upload -p /dev/cu.usbmodem101 --fqbn "$FQBN" hello_c6
```

### If an upload fails with "Failed to connect ... No serial data received"
1. Unplug the USB cable.
2. Hold the **BOOT** button.
3. Plug the cable back in while holding BOOT.
4. Let go and upload again.

This was needed only for the first upload. Once our code is running, uploads work straight from the laptop.

### Pins
| Use | GPIO |
|---|---|
| Onboard LED (taken) | 14 |
| Ultrasonic Trig | 4 |
| Ultrasonic Echo | 5 (through a 1k/2k voltage divider) |
| Servo | 6 |

### Open question: 5V power
PCB Cupid's overview describes the board as 3.3V logic and power and doesn't mention a 5V pin. The HC-SR04 and the SG90 servos both need 5V. Check the board for a pin labeled **5V** or **VBUS**. If there isn't one, use a separate 5V supply and connect its ground to the board's GND.

---

## Box firmware (`dog_box/`, uploaded and tested 2026-09-27)

For now the laptop talks to the box over the USB cable (115200 baud), not WiFi. Send one letter, get one line back:

| Send | Box does | Reply |
|---|---|---|
| `P` | ping | `OK` |
| `D` | ultrasonic distance | `D 42` (cm), `D -1` if nothing is wired or detected |
| `T` | treat servo (GPIO 6) turns to 60°, holds 400 ms, returns | `T done` |
| `B` | ball servo (GPIO 7) turns to 90°, holds 1 s, returns | `B done` |

The onboard LED lights during `T` and `B`, so it can be tested before servos are connected. Echo has a pull-down so an unwired sensor reads `-1` instead of noise.

## Tools
- **PCB Cupid docs MCP** is added to Claude Code (user scope): `https://learn.pcbcupid.com/mcp`. It searches their guides and becomes available after restarting Claude Code.

## Status (2026-09-27)
- `dog_box/`: firmware on the board, all 4 commands tested.
- `brain/`: loop, Claude classifier, ladder, step-1 `label_test.py` built. 12 tests pass; dry run works; real box + mic work.
- `owner/`: stats, daily report (Claude + `--no-llm` fallback), Telegram notify, placeholder voices. 4 tests pass. See `owner/SETUP.md`.

## Blockers (human steps)
1. ~~Anthropic API key~~ done: saved in `owner/.env` (private, gitignored). Both brain and owner read it. **$20 spend cap** in `budget.py`: every Claude call is checked first and its real cost added to `spend.json`; at the cap the brain alerts the owner and stops, and the report falls back to the plain version. Check spend: `.venv/bin/python budget.py`. Measured: ~$0.001 per single-photo look, ~$0.003 per live look (3 photos), ~$0.014 per daily report.
2. **Camera permission:** System Settings > Privacy & Security > Camera > allow your terminal app, then restart the terminal.
3. **Telegram:** create a new bot with @BotFather (steps in `owner/SETUP.md`).
4. **Real voice clips:** record on the owner's phone, AirDrop into `voices/`, delete the placeholders.
5. **Hardware:** HC-SR04 wired and reading real distances (2026-09-27). 5V answered: servos + sensor run on a 5V 1A adapter with GND shared to the board (the board also has a **USB** 5V pin, left side pin 10). Still to do: buy and wire 2 SG90 servos (D6, D7). Tune `BARK_LOUD` in `brain/sense.py` (a quiet room reads ~0.064 against a 0.1 threshold).

## Next step
Once the key works: run `brain/label_test.py` on real dog clips (README step 1). That's the go/no-go test.

## Dog screen (`dogscreen/`)
Full-screen page the dog sees. The brain writes `dogscreen/now.json` before each voice/treat/ball; the page polls it every second.
- Idle: nearly dark. Voice: owner photo (`dogscreen/owner.jpg`). Treat: yellow flash + two-note "good dog" chime. Ball: yellow ball rolling on blue. Blue and yellow only (what dogs see best).
- Run: `.venv/bin/python -m http.server 8000 -d dogscreen`, open http://localhost:8000, tap once (browsers need a tap before sound). Keys 1/2/3/0 preview voice/treat/ball/idle.

## Ask the bot (`owner/ask_bot.py`)
Buttons under the chat: **🐶 What's he doing?** (fresh photo + Claude's read + today's summary), **🔊 Voice / 🦴 Treat / 🎾 Ball** (the device does it now, the dog screen shows it, logged with trigger `owner` so the report counts it). A treat while the dog is anxious gets a gentle tip. The brain and bot share the box through a lock (`/tmp/dogbox.lock`). Only the owner's chat id gets answers. ~$0.003 per ask, counted in the $20 cap.
Run and leave running: `.venv/bin/python -m owner.ask_bot`

## Always live: `./start.sh` / `./stop.sh`
`./start.sh` (from a terminal with camera + mic permission) starts the dog screen server, the Telegram bot, the brain and `caffeinate` (no sleep) in the background, skipping anything already running, and opens the dog screen in its own full-screen Chrome window that may play sound without a tap. `./stop.sh` stops all of it. Logs and pids: `logs/run/`. The brain costs ~$0.5-1/day in Claude calls while running (capped at $20).
