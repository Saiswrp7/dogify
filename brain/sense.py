"""Webcam frames and mic loudness: the laptop's eyes and ears.

Try it:  python sense.py   (prints mic loudness for 10 s, then saves one webcam frame)
Use the printed numbers to tune BARK_LOUD: quiet room vs. someone barking at the laptop.
"""
import tempfile
import time
from pathlib import Path

import cv2
import numpy as np
import sounddevice as sd

BARK_LOUD = 0.1   # mic loudness (0 to 1) at or above this counts as barking. Tune it!
MAX_SIDE = 768    # shrink frames before sending them to Claude: fewer tokens, lower cost

CAMERA_HELP = ("Could not read the webcam. On macOS, allow camera access for your terminal app "
               "in System Settings > Privacy & Security > Camera, then restart the terminal.")
MIC_HELP = ("On macOS, allow microphone access for your terminal app in "
            "System Settings > Privacy & Security > Microphone, then restart the terminal.")


class SenseError(Exception):
    """The camera or mic could not be used. The message says how to fix it."""


def to_jpeg(image):
    """OpenCV image -> JPEG bytes, shrunk so the longest side is at most MAX_SIDE."""
    height, width = image.shape[:2]
    scale = MAX_SIDE / max(height, width)
    if scale < 1:
        image = cv2.resize(image, (int(width * scale), int(height * scale)))
    ok, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return buffer.tobytes()


def grab_frames(n=3, gap_s=5, camera=0):
    """Take n webcam photos, gap_s seconds apart. Returns a list of JPEG bytes."""
    cam = cv2.VideoCapture(camera)
    if not cam.isOpened():
        raise SenseError(CAMERA_HELP)
    frames = []
    try:
        for i in range(n):
            if i > 0:
                time.sleep(gap_s)
            for _ in range(5):  # read a few: the first frames after a pause are dark or old
                ok, image = cam.read()
            if not ok:
                raise SenseError(CAMERA_HELP)
            frames.append(to_jpeg(image))
    finally:
        cam.release()
    return frames


def bark_level(seconds=1, rate=16000):
    """Record the mic for a moment and return its loudness (RMS, 0 = silent, 1 = max)."""
    try:
        audio = sd.rec(int(seconds * rate), samplerate=rate, channels=1, dtype="float32")
        sd.wait()
    except sd.PortAudioError as e:
        raise SenseError(f"Microphone error: {e}. {MIC_HELP}")
    if not audio.any():  # a real mic is never exactly zero; macOS sends zeros when access is denied
        raise SenseError("The microphone returned pure silence. " + MIC_HELP)
    return float(np.sqrt(np.mean(audio ** 2)))


if __name__ == "__main__":
    print(f"Mic loudness for 10 s (barking threshold is {BARK_LOUD}):")
    for _ in range(10):
        level = bark_level()
        print(f"  {level:.3f}  {'#' * int(level * 200)}")
    frame = grab_frames(n=1)[0]
    path = Path(tempfile.gettempdir()) / "dog_test_frame.jpg"
    path.write_bytes(frame)
    print(f"Saved a webcam frame ({len(frame)} bytes) to {path}")
