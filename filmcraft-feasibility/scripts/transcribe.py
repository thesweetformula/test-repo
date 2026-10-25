#!/usr/bin/env python3
"""Transcribe work/synthetic.mp4 to word timestamps with faster-whisper on CPU."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# PyAV 19 dropped the metadata_errors keyword that faster-whisper 1.2.1 still passes.
import av

_av_open = av.open


def _av_open_compat(*args, **kwargs):
    kwargs.pop("metadata_errors", None)
    return _av_open(*args, **kwargs)


av.open = _av_open_compat

from faster_whisper import WhisperModel  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import WORK, ensure_work, headless_env  # noqa: E402


def main() -> None:
    ensure_work()
    os.environ.update(headless_env())
    os.environ.setdefault("HF_HOME", str(WORK / "hf-cache"))
    media = WORK / "synthetic.mp4"
    if not media.exists():
        raise SystemExit(f"missing {media}; run scripts/make_synthetic.sh first")

    # base int8 mis-heard this espeak clip ("Stress hits your gut" -> "Just rest it").
    # small int8 got the spoken lines. Override with WHISPER_MODEL if you need the faster one.
    model_name = os.environ.get("WHISPER_MODEL", "small")
    started = time.perf_counter()
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    load_s = time.perf_counter() - started
    transcribe_started = time.perf_counter()
    segments, info = model.transcribe(
        str(media),
        word_timestamps=True,
        language="en",
        vad_filter=False,
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
    transcribe_s = time.perf_counter() - transcribe_started
    payload = {
        "model": model_name,
        "device": "cpu",
        "compute_type": "int8",
        "language": info.language,
        "duration": info.duration,
        "load_seconds": round(load_s, 3),
        "transcribe_seconds": round(transcribe_s, 3),
        "segments": dumped,
    }
    (WORK / "transcript.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"whisper {model_name} load {load_s:.2f}s transcribe {transcribe_s:.2f}s "
        f"audio {info.duration:.2f}s segments {len(dumped)}"
    )
    for seg in dumped:
        print(f"  {seg['start']:.2f}-{seg['end']:.2f} {seg['text']}")


if __name__ == "__main__":
    main()
