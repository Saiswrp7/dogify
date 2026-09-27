"""Talk to the ESP32 dog box over USB.

Protocol (see dog_box/dog_box.ino): send one letter, get one line back.
  P -> OK      D -> D <cm>  (D -1 = nothing detected)
  T -> T done  (drop a treat)
  B -> B done  (roll the ball)

Try it:  python box.py
"""
import fcntl
import glob
import random
import time

import serial

# The name changes with the USB port used (usbmodem101, usbmodem1101, ...), so find it.
PORT = (sorted(glob.glob("/dev/cu.usbmodem*")) or ["/dev/cu.usbmodem101"])[0]
LOCK = "/tmp/dogbox.lock"  # the brain and the Telegram bot both talk to the box; one at a time


class Box:
    def __init__(self, port=PORT, baud=115200):
        self.serial = serial.Serial(port, baud, timeout=3)
        time.sleep(1.5)                  # give the board a moment after opening the port
        self.serial.reset_input_buffer()  # throw away anything it printed before

    def _ask(self, letter):
        with open(LOCK, "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)     # wait if the other program is mid-command
            self.serial.reset_input_buffer()     # drop any stray reply meant for the other program
            self.serial.write(letter.encode())
            return self.serial.readline().decode(errors="replace").strip()

    def ping(self):
        return self._ask("P") == "OK"

    def distance(self):
        """Distance in cm, or -1 if nothing was detected (or the sensor isn't wired)."""
        reply = self._ask("D")  # e.g. "D 37"
        try:
            return int(reply.split()[1])
        except (IndexError, ValueError):
            return -1

    def treat(self):
        return self._ask("T") == "T done"

    def ball(self):
        return self._ask("B") == "B done"


class FakeBox:
    """Stands in for the real box in tests and --dry-run. Prints instead of moving."""

    def ping(self):
        return True

    def distance(self):
        return random.choice([-1, -1, -1, 25, 120])

    def treat(self):
        print("  (fake box) treat dropped")
        return True

    def ball(self):
        print("  (fake box) ball rolled")
        return True


if __name__ == "__main__":
    box = Box()
    print("ping:", box.ping())
    print("distance:", box.distance(), "cm")
