"""Original background track for the Dogify video: playful plucked arpeggios, soft beat, warm bass.
F major, I-V-vi-IV (F C Dm Bb), 104 BPM. Writes ../public/music.wav.  Run: python compose.py [seconds]"""
import sys, wave
import numpy as np

SR, BPM = 44100, 104
LENGTH = float(sys.argv[1]) if len(sys.argv) > 1 else 68.0
beat = 60 / BPM
bar = 4 * beat
n = int(LENGTH * SR)
mix = np.zeros((n, 2))
rng = np.random.default_rng(7)


def note_hz(midi):
    return 440 * 2 ** ((midi - 69) / 12)


def add(sig, t, pan=0.0, gain=1.0):
    i = int(t * SR)
    if i >= n:
        return
    sig = sig[: n - i] * gain
    mix[i:i + len(sig), 0] += sig * (1 - max(pan, 0))
    mix[i:i + len(sig), 1] += sig * (1 + min(pan, 0))


def pluck(midi, dur=0.45):
    t = np.arange(int(dur * SR)) / SR
    f = note_hz(midi)
    tone = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) + 0.12 * np.sin(2 * np.pi * 3 * f * t)
    env = np.exp(-t * 9) * np.minimum(1, t * 400)
    return tone * env * 0.22


def bell(midi, dur=0.9):
    t = np.arange(int(dur * SR)) / SR
    f = note_hz(midi)
    tone = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t * 6)
    return tone * np.exp(-t * 4) * np.minimum(1, t * 600) * 0.16


def bass(midi, dur):
    t = np.arange(int(dur * SR)) / SR
    f = note_hz(midi)
    tone = np.tanh(1.6 * (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)))
    return tone * np.exp(-t * 2.2) * np.minimum(1, t * 200) * 0.30


def kick():
    t = np.arange(int(0.35 * SR)) / SR
    f = 110 * np.exp(-t * 18) + 45
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) * 0.55


def snap():
    t = np.arange(int(0.18 * SR)) / SR
    noise = rng.standard_normal(len(t))
    noise = np.convolve(noise, [1, -0.9], "same")  # brighten
    return noise * np.exp(-t * 28) * 0.10


def hat():
    t = np.arange(int(0.05 * SR)) / SR
    noise = np.diff(rng.standard_normal(len(t) + 1))
    return noise * np.exp(-t * 90) * 0.035


# F  C  Dm  Bb   (root midi, chord tones)
CHORDS = [(53, [65, 69, 72, 77]), (48, [64, 67, 72, 76]), (50, [65, 69, 74, 77]), (46, [65, 70, 74, 77])]
ARP = [0, 1, 2, 3, 2, 1, 2, 1]                   # 8th-note pattern over the 4 chord tones
MELODY = [(0, 81), (1.5, 79), (2, 77), (3, 76),  # a little bell hook, beats within a 4-bar phrase
          (4, 76), (5.5, 77), (6, 79), (8, 74), (9.5, 76), (10, 77), (12, 77), (13, 76), (14, 72)]

bars = int(LENGTH / bar) + 1
for b in range(bars):
    t0 = b * bar
    root, tones = CHORDS[b % 4]
    for k, idx in enumerate(ARP):                               # plucks, lightly panned
        add(pluck(tones[idx]), t0 + k * beat / 2, pan=0.3 if k % 2 else -0.3)
    if b >= 2:                                                  # rhythm section enters on bar 3
        add(bass(root, beat * 1.8), t0)
        add(bass(root + 7 if b % 2 else root, beat * 1.8), t0 + 2 * beat)
        for q in (0, 2):
            add(kick(), t0 + q * beat)
        for q in (1, 3):
            add(snap(), t0 + q * beat, pan=0.1)
        for e in range(8):
            add(hat(), t0 + e * beat / 2 + (0.012 if e % 2 else 0), pan=-0.2)
    if b >= 4 and (b // 4) % 2 == 1:                            # bell hook every other phrase
        for at, m in MELODY:
            if int(at // 4) == b % 4:
                add(bell(m), t0 + (at % 4) * beat, pan=0.15)

# soft fade in and a 3 s fade out, then normalise
fade = np.ones(n)
fade[: SR] = np.linspace(0, 1, SR)
fade[-3 * SR:] = np.linspace(1, 0, 3 * SR)
mix *= fade[:, None]
mix = mix / np.max(np.abs(mix)) * 0.89

pcm = (mix * 32767).astype(np.int16)
with wave.open("../public/music.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print(f"wrote ../public/music.wav  {LENGTH:.1f}s")
