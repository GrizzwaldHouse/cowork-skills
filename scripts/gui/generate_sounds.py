# generate_sounds.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: Synthesize owl-themed audio cues to avoid external dependencies and licensing issues

"""
Generate short WAV sound effects for OwlWatcher.

Creates 4 sounds in scripts/gui/assets/sounds/:
- startup_hoot.wav   — warm rising tone (owl waking up)
- alert_chirp.wav    — quick attention chirp
- alarm_hoot.wav     — urgent double-hoot
- allclear_settle.wav — gentle descending settle tone

All files are 16-bit mono PCM at 22050 Hz, under 50 KB each.

Run directly::

    python scripts/gui/generate_sounds.py
"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

SOUNDS_DIR = Path(__file__).resolve().parent / "assets" / "sounds"
SAMPLE_RATE = 22050
CHANNELS = 1
SAMPLE_WIDTH = 2  # bytes (16-bit)
MAX_AMP = 30000


def _sine_wave(freq: float, duration: float, volume: float = 1.0) -> list[int]:
    """Generate samples for a sine wave tone."""
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        # Apply fade-in/out envelope (10ms)
        env = 1.0
        fade_samples = int(0.01 * SAMPLE_RATE)
        if i < fade_samples:
            env = i / fade_samples
        elif i > n - fade_samples:
            env = (n - i) / fade_samples
        val = math.sin(2 * math.pi * freq * t) * MAX_AMP * volume * env
        samples.append(int(val))
    return samples


def _write_wav(path: Path, samples: list[int]) -> None:
    """Write samples to a 16-bit mono WAV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        data = struct.pack(f"<{len(samples)}h", *samples)
        wf.writeframes(data)
    print(f"  Created: {path.name} ({path.stat().st_size} bytes)")


def generate_startup_hoot() -> None:
    """Warm rising tone: 300Hz -> 500Hz over 0.4s."""
    n = int(SAMPLE_RATE * 0.4)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = i / n
        freq = 300 + 200 * progress
        env = 1.0
        fade = int(0.02 * SAMPLE_RATE)
        if i < fade:
            env = i / fade
        elif i > n - fade:
            env = (n - i) / fade
        val = math.sin(2 * math.pi * freq * t) * MAX_AMP * 0.6 * env
        samples.append(int(val))
    _write_wav(SOUNDS_DIR / "startup_hoot.wav", samples)


def generate_alert_chirp() -> None:
    """Quick attention chirp: 800Hz for 0.1s."""
    samples = _sine_wave(800, 0.1, volume=0.5)
    _write_wav(SOUNDS_DIR / "alert_chirp.wav", samples)


def generate_alarm_hoot() -> None:
    """Urgent double-hoot: two 400Hz tones separated by 0.08s silence."""
    hoot = _sine_wave(400, 0.15, volume=0.7)
    silence = [0] * int(SAMPLE_RATE * 0.08)
    samples = hoot + silence + hoot
    _write_wav(SOUNDS_DIR / "alarm_hoot.wav", samples)


def generate_allclear_settle() -> None:
    """Gentle descending tone: 600Hz -> 350Hz over 0.3s."""
    n = int(SAMPLE_RATE * 0.3)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = i / n
        freq = 600 - 250 * progress
        env = 1.0
        fade = int(0.02 * SAMPLE_RATE)
        if i < fade:
            env = i / fade
        elif i > n - fade:
            env = (n - i) / fade
        val = math.sin(2 * math.pi * freq * t) * MAX_AMP * 0.4 * env
        samples.append(int(val))
    _write_wav(SOUNDS_DIR / "allclear_settle.wav", samples)


def main() -> None:
    """Generate all sound effects."""
    print("Generating OwlWatcher sound effects...")
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    generate_startup_hoot()
    generate_alert_chirp()
    generate_alarm_hoot()
    generate_allclear_settle()
    print("Done.")


if __name__ == "__main__":
    main()
