"""Generate the Chinese voiceover and SRT from captions.json.

Requires edge-tts (network) and ffmpeg. The TTS segments are placed at the
caption start times and mixed into one 52s track for Remotion.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import wave
from pathlib import Path

import edge_tts
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CAPTIONS_PATH = ROOT / "captions.json"
SEGMENT_DIR = ROOT / "out" / "vo-segments"
VOICEOVER = ROOT / "public" / "audio" / "voiceover.mp3"
SRT_PATH = ROOT / "out" / "mpux-promo.srt"
VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "+8%"
SAMPLE_RATE = 48_000
DURATION = 52.0


def run(command: list[str]) -> None:
    subprocess.run(command, check=True, capture_output=True)


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        sample_rate = handle.getframerate()
        frames = handle.readframes(handle.getnframes())
    data = np.frombuffer(frames, dtype="<i2").reshape(-1, channels)
    return data.astype(np.float64) / 32768.0, sample_rate


def srt_time(seconds: float) -> str:
    total_ms = max(0, round(seconds * 1000))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


async def synthesize(text: str, output: Path) -> None:
    communicator = edge_tts.Communicate(text, VOICE, rate=RATE)
    await communicator.save(str(output))


def main() -> None:
    captions = json.loads(CAPTIONS_PATH.read_text(encoding="utf-8"))
    SEGMENT_DIR.mkdir(parents=True, exist_ok=True)
    SRT_PATH.parent.mkdir(parents=True, exist_ok=True)

    clips: list[np.ndarray] = []
    for index, item in enumerate(captions):
        mp3_path = SEGMENT_DIR / f"{index:02d}.mp3"
        wav_path = SEGMENT_DIR / f"{index:02d}.wav"
        asyncio.run(synthesize(item["text"], mp3_path))
        duration = probe_duration(mp3_path)
        item["end"] = round(item["start"] + duration + 0.25, 2)
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(mp3_path),
                "-ar",
                str(SAMPLE_RATE),
                "-ac",
                "2",
                str(wav_path),
            ]
        )
        clip, sample_rate = read_wav(wav_path)
        if sample_rate != SAMPLE_RATE:
            raise RuntimeError(f"Unexpected sample rate: {sample_rate}")
        clips.append(clip)
        print(f"{index:02d}  {item['start']:5.1f}s  {duration:4.2f}s  {item['text']}")

    for first, second in zip(captions, captions[1:]):
        if first["end"] > second["start"]:
            print(
                f"WARNING overlapping voiceover: {first['start']}-{first['end']} "
                f"vs next {second['start']}"
            )

    total_samples = int(DURATION * SAMPLE_RATE)
    mix = np.zeros((total_samples, 2), dtype=np.float64)
    for item, clip in zip(captions, clips):
        start = int(item["start"] * SAMPLE_RATE)
        if start >= total_samples:
            continue
        take = min(len(clip), total_samples - start)
        mix[start : start + take] += clip[:take]

    peak = float(np.max(np.abs(mix)))
    if peak > 0.95:
        mix *= 0.95 / peak
    samples = np.clip(mix * 32767.0, -32768, 32767).astype("<i2")
    mix_wav = SEGMENT_DIR / "voiceover.wav"
    with wave.open(str(mix_wav), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(samples.tobytes())
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(mix_wav),
            "-codec:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(VOICEOVER),
        ]
    )

    CAPTIONS_PATH.write_text(
        json.dumps(captions, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lines: list[str] = []
    for index, item in enumerate(captions, start=1):
        lines.extend(
            [
                str(index),
                f"{srt_time(item['start'])} --> {srt_time(min(item['end'], DURATION))}",
                item["text"],
                "",
            ]
        )
    SRT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {VOICEOVER}")
    print(f"Wrote {SRT_PATH}")
    print(f"Wrote {CAPTIONS_PATH}")


if __name__ == "__main__":
    main()
