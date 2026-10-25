#!/usr/bin/env python3
"""Transcribe the Week 48 proxies with faster-whisper on CPU.

Expects gitignored files:

  work/week48/raw.mp4
  work/week48/final.mp4

`small` is the default because, on the human final, it kept the stretches that
`medium` skipped and it agreed with the burned-in captions where those captions
were readable. Set WHISPER_MODEL=medium to write a separate cross-check file.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import av

_av_open = av.open


def _av_open_compat(*args, **kwargs):
    kwargs.pop("metadata_errors", None)
    return _av_open(*args, **kwargs)


av.open = _av_open_compat

from faster_whisper import WhisperModel  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import WORK, headless_env  # noqa: E402

WEEK = WORK / "week48"


def transcribe(model: WhisperModel, model_name: str, media: Path) -> dict:
    started = time.perf_counter()
    segments, info = model.transcribe(
        str(media),
        word_timestamps=True,
        language="en",
        vad_filter=False,
        beam_size=5,
    )
    dumped = []
    for index, seg in enumerate(segments):
        words = []
        for word in seg.words or []:
            words.append(
                {
                    "word": word.word.strip(),
                    "start": round(float(word.start), 3),
                    "end": round(float(word.end), 3),
                    "prob": round(float(word.probability), 3),
                    "segment": index,
                }
            )
        dumped.append(
            {
                "segment": index,
                "start": round(float(seg.start), 3),
                "end": round(float(seg.end), 3),
                "text": seg.text.strip(),
                "words": words,
            }
        )
    return {
        "file": media.name,
        "model": model_name,
        "device": "cpu",
        "compute_type": "int8",
        "language": info.language,
        "duration": info.duration,
        "seconds": round(time.perf_counter() - started, 3),
        "segments": dumped,
    }


def main() -> None:
    os.environ.update(headless_env())
    os.environ.setdefault("HF_HOME", str(WORK / "hf-cache"))
    model_name = os.environ.get("WHISPER_MODEL", "small")
    WEEK.mkdir(parents=True, exist_ok=True)
    paths = [WEEK / "raw.mp4", WEEK / "final.mp4"]
    missing = [path for path in paths if not path.exists()]
    if missing:
        raise SystemExit("missing " + ", ".join(str(path) for path in missing))

    load_started = time.perf_counter()
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    load_s = time.perf_counter() - load_started
    for media in paths:
        payload = transcribe(model, model_name, media)
        payload["load_seconds"] = round(load_s, 3)
        if model_name == "small":
            out = WEEK / f"transcript_{media.stem}.json"
        else:
            out = WEEK / f"transcript_{media.stem}_{model_name}.json"
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        words = [word for seg in payload["segments"] for word in seg["words"]]
        mean = sum(word["prob"] for word in words) / max(len(words), 1)
        print(
            f"{media.name} {model_name} {payload['seconds']:.1f}s "
            f"words {len(words)} mean_prob {mean:.3f} -> {out.name}"
        )
        for seg in payload["segments"]:
            print(f"  {seg['start']:.2f}-{seg['end']:.2f} {seg['text']}")


if __name__ == "__main__":
    main()
