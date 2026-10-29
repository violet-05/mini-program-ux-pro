"""Generate a soft 52s ambient bed for the MPUX promo.

No external samples or network. The output is intentionally quiet and consonant so
the visuals carry the message; replace public/audio/bed.mp3 to change the mood.
"""

from __future__ import annotations

import math
import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 44_100
DURATION = 52.0
N = int(SAMPLE_RATE * DURATION)
SEGMENT = DURATION / 8
OUT = Path(__file__).resolve().parents[1] / "public" / "audio" / "bed.mp3"

# Am9 / Fmaj7 / Cmaj9 / G6, resolved to Am9 at the end.
CHORDS = [
    (110.00, 130.81, 164.81, 246.94),
    (87.31, 110.00, 130.81, 164.81),
    (130.81, 164.81, 196.00, 293.66),
    (98.00, 123.47, 146.83, 164.81),
    (110.00, 130.81, 164.81, 246.94),
    (87.31, 110.00, 130.81, 164.81),
    (130.81, 164.81, 196.00, 293.66),
    (110.00, 130.81, 164.81, 246.94),
]


def smoothstep(value: np.ndarray) -> np.ndarray:
    clipped = np.clip(value, 0.0, 1.0)
    return clipped * clipped * (3.0 - 2.0 * clipped)


def main() -> None:
    t = np.arange(N, dtype=np.float64) / SAMPLE_RATE
    mix = np.zeros((N, 2), dtype=np.float64)
    rng = np.random.default_rng(7)

    for index, frequencies in enumerate(CHORDS):
        start = index * SEGMENT
        local = t - start
        attack = smoothstep((local + 0.9) / 2.4)
        release = smoothstep((SEGMENT + 0.9 - local) / 2.8)
        envelope = attack * release
        active = envelope > 0
        if not active.any():
            continue

        for voice, frequency in enumerate(frequencies):
            pan = 0.5 + (voice - 1.5) * 0.09
            gain = 0.045 if voice else 0.06
            for detune, phase, stereo_bias in (
                (-0.11, 0.0, 0.5),
                (0.11, math.pi * 0.37, -0.5),
            ):
                oscillator = np.sin(
                    2.0 * math.pi * (frequency + detune) * t[active] + phase
                )
                contribution = envelope[active] * oscillator * gain
                mix[active, 0] += contribution * (pan + stereo_bias * 0.035)
                mix[active, 1] += contribution * (1.0 - pan - stereo_bias * 0.035)

        root = frequencies[0]
        sub = np.sin(2.0 * math.pi * (root / 2.0) * t[active])
        mix[active, 0] += envelope[active] * sub * 0.028
        mix[active, 1] += envelope[active] * sub * 0.028

        shimmer = np.sin(2.0 * math.pi * frequencies[1] * 4.0 * t[active])
        mix[active, 0] += envelope[active] * shimmer * 0.004
        mix[active, 1] += envelope[active] * shimmer * 0.004

    air = rng.normal(0.0, 1.0, N)
    # A cheap low-pass: moving average over 24 samples.
    kernel = np.ones(24, dtype=np.float64) / 24.0
    air = np.convolve(air, kernel, mode="same")
    mix[:, 0] += air * 0.010
    mix[:, 1] += np.roll(air, 137) * 0.010

    lfo = 0.86 + 0.14 * np.sin(2.0 * math.pi * 0.055 * t)
    mix *= lfo[:, None]

    fade_in = smoothstep(t / 2.5)
    fade_out = smoothstep((DURATION - t) / 3.5)
    mix *= (fade_in * fade_out)[:, None]

    peak = float(np.max(np.abs(mix)))
    if peak > 0:
        mix *= 0.30 / peak
    samples = np.clip(mix * 32767.0, -32768, 32767).astype("<i2")

    wav_path = OUT.with_suffix(".wav")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(wav_path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(samples.tobytes())
    print(f"Wrote {wav_path} ({DURATION:.0f}s, peak {peak:.3f})")

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(wav_path),
                "-codec:a",
                "libmp3lame",
                "-b:a",
                "192k",
                str(OUT),
            ],
            check=True,
        )
        wav_path.unlink()
        print(f"Wrote {OUT}")
    else:
        print("ffmpeg not found; encode the WAV manually or install ffmpeg.")


if __name__ == "__main__":
    main()
