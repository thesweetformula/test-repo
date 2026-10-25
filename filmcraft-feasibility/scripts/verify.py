#!/usr/bin/env python3
"""Confirm the export plays, is 1080x1920 H.264, and show captions plus a zoom."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

from common import WORK, ensure_work


def ffprobe(path: Path) -> dict:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(proc.stdout)


def read_rgb(path: Path) -> np.ndarray:
    meta = ffprobe(path)
    stream = next(stream for stream in meta["streams"] if stream["codec_type"] == "video")
    width = int(stream["width"])
    height = int(stream["height"])
    raw = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ],
        check=True,
        capture_output=True,
    ).stdout
    frame = np.frombuffer(raw, dtype=np.uint8)
    if frame.size != width * height * 3:
        raise RuntimeError(f"{path} decoded to {frame.size} bytes, expected {width * height * 3}")
    return frame.reshape((height, width, 3))


def white_mask(image: np.ndarray) -> np.ndarray:
    return np.logical_and(np.all(image >= 230, axis=2), np.any(image > 245, axis=2))


def white_count(image: np.ndarray) -> int:
    return int(white_mask(image).sum())


def yellow_count(image: np.ndarray) -> int:
    red = image[:, :, 0] > 210
    green = image[:, :, 1] > 190
    blue = image[:, :, 2] < 80
    return int(np.logical_and(np.logical_and(red, green), blue).sum())


def cue_times(path: Path) -> list[tuple[float, float, str]]:
    cues = []
    blocks = path.read_text(encoding="utf-8").strip().split("\n\n")
    for block in blocks:
        lines = [line for line in block.splitlines() if line.strip()]
        if len(lines) < 3 or "-->" not in lines[1]:
            continue
        start_s, end_s = lines[1].split("-->")
        cues.append((parse_ts(start_s), parse_ts(end_s), lines[2]))
    return cues


def parse_ts(value: str) -> float:
    hours, minutes, rest = value.strip().split(":")
    seconds, millis = rest.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000


def integrated_loudness(path: Path) -> float | None:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    for line in proc.stderr.splitlines():
        stripped = line.strip()
        if stripped.startswith("I:"):
            return float(stripped.split()[1])
    return None


def extract_frame(video: Path, seconds: float, dest: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-ss",
            f"{seconds:.3f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            str(dest),
        ],
        check=True,
    )


def main() -> None:
    ensure_work()
    report = json.loads((WORK / "edit-report.json").read_text(encoding="utf-8"))
    export = WORK / "export.mp4"
    probed = ffprobe(export)
    video = next(stream for stream in probed["streams"] if stream["codec_type"] == "video")
    audio = next(stream for stream in probed["streams"] if stream["codec_type"] == "audio")
    duration = float(probed["format"]["duration"])
    expected = float(report["timeline_seconds"])
    frames_dir = WORK / "frames"
    frames_dir.mkdir(exist_ok=True)
    cues = cue_times(WORK / "captions.srt")
    if len(cues) < 2:
        raise RuntimeError(f"expected word cues in captions.srt, found {len(cues)}")
    early_t = min(0.25, expected * 0.1)
    late_t = max(early_t, expected - 0.3)
    caption_t = (cues[0][0] + cues[0][1]) / 2
    late_caption_t = (cues[-1][0] + cues[-1][1]) / 2
    early_path = frames_dir / "early.png"
    mid_path = frames_dir / "caption.png"
    late_path = frames_dir / "late.png"
    extract_frame(export, early_t, early_path)
    extract_frame(export, caption_t, mid_path)
    extract_frame(export, late_t, late_path)
    extract_frame(export, late_caption_t, frames_dir / "caption-late.png")

    early = read_rgb(early_path)
    late = read_rgb(late_path)
    mid = read_rgb(mid_path)
    height = early.shape[0]
    top = slice(0, int(height * 0.12))
    bottom = slice(int(height * 0.72), int(height * 0.92))

    late_caption = read_rgb(frames_dir / "caption-late.png")
    checks = {
        "caption_sample": cues[0][2],
        "caption_sample_time": round(caption_t, 3),
        "late_caption_sample": cues[-1][2],
        "video_codec": video["codec_name"],
        "audio_codec": audio["codec_name"],
        "width": int(video["width"]),
        "height": int(video["height"]),
        "pix_fmt": video.get("pix_fmt"),
        "frame_rate": video.get("avg_frame_rate"),
        "duration": duration,
        "expected_duration": expected,
        "encoder": probed["format"].get("tags", {}).get("encoder"),
        "early_yellow": yellow_count(early),
        "late_yellow": yellow_count(late),
        "mid_bottom_white": white_count(mid[bottom]),
        "mid_top_white": white_count(mid[top]),
        "late_bottom_white": white_count(late_caption[bottom]),
        "late_top_white": white_count(late_caption[top]),
    }
    problems = []
    if checks["video_codec"] != "h264":
        problems.append(f"video codec is {checks['video_codec']}")
    if checks["audio_codec"] != "aac":
        problems.append(f"audio codec is {checks['audio_codec']}")
    if (checks["width"], checks["height"]) != (1080, 1920):
        problems.append(f"frame size is {checks['width']}x{checks['height']}")
    if abs(duration - expected) > 0.08:
        problems.append(f"duration {duration:.3f}s vs edited timeline {expected:.3f}s")
    if checks["late_yellow"] < checks["early_yellow"] * 1.15:
        problems.append(
            f"yellow center did not grow (early {checks['early_yellow']} late {checks['late_yellow']}); zoom not visible"
        )
    caption_white = max(checks["mid_bottom_white"], checks["late_bottom_white"])
    caption_top = max(checks["mid_top_white"], checks["late_top_white"])
    if caption_white < 400 or caption_white < caption_top * 4:
        problems.append(
            f"burned-in captions not detected (bottom white {caption_white}, top white {caption_top})"
        )
    loudness = integrated_loudness(export)
    checks["integrated_lufs"] = loudness
    if loudness is None:
        problems.append("could not read integrated loudness")
    elif abs(loudness - (-14.0)) > 1.5:
        problems.append(f"integrated loudness {loudness:.1f} LUFS is outside -14 ± 1.5")
    white_rows = np.flatnonzero(white_mask(mid).any(axis=1))
    checks["caption_white_row_fraction"] = (
        round(float(white_rows.mean()) / height, 3) if white_rows.size else None
    )
    checks["problems"] = problems
    checks["ok"] = not problems
    (WORK / "verify.json").write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(checks, indent=2))
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
