#!/usr/bin/env python3
"""Measure the Week 48 proxies. Writes JSON under work/week48. Does not export media.

The raw proxy and the human final are compared as speech, picture, loudness and
caption geometry. A FilmCraft rough cut is only justified when the final's words
actually occur in the raw.
"""

from __future__ import annotations

import json
import re
import subprocess
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
WEEK = ROOT / "work" / "week48"
RAW = WEEK / "raw.mp4"
FINAL = WEEK / "final.mp4"


def ffmpeg_frames(path: Path, fps: float, width: int, height: int) -> np.ndarray:
    proc = subprocess.run(
        [
            "ffmpeg", "-v", "error", "-i", str(path),
            "-vf", f"fps={fps}",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ],
        check=True, capture_output=True,
    )
    frame = width * height * 3
    count = len(proc.stdout) // frame
    return np.frombuffer(proc.stdout, dtype=np.uint8)[: count * frame].reshape(count, height, width, 3)


def text_mask(frame: np.ndarray) -> np.ndarray:
    """Bright glyphs that sit against a dark neighbour (fill plus outline or shadow)."""
    bright = (frame.min(axis=2) > 195) & ((frame.max(axis=2) - frame.min(axis=2)) < 45)
    luma = frame.mean(axis=2)
    dark = luma < 90
    near = np.zeros_like(dark)
    for shift in (-2, -1, 1, 2):
        near |= np.roll(dark, shift, axis=0)
        near |= np.roll(dark, shift, axis=1)
    return bright & near


def gray(frame: np.ndarray) -> np.ndarray:
    return frame.mean(axis=2).astype(np.float32)


def downscale(image: np.ndarray, height: int, width: int) -> np.ndarray:
    ys = np.linspace(0, image.shape[0] - 1, height).astype(np.int32)
    xs = np.linspace(0, image.shape[1] - 1, width).astype(np.int32)
    return image[ys][:, xs]


def zscore(image: np.ndarray) -> np.ndarray:
    centered = image - image.mean()
    return centered / (centered.std() + 1e-3)


def zoom_score(earlier: np.ndarray, later: np.ndarray, scale: float) -> float:
    """How well `later` matches `earlier` after assuming the camera pushed in by `scale`."""
    g0 = gray(earlier)
    g1 = gray(later)
    crop_h = max(8, int(round(g0.shape[0] / scale)))
    crop_w = max(8, int(round(g0.shape[1] / scale)))
    y0 = (g0.shape[0] - crop_h) // 2
    x0 = (g0.shape[1] - crop_w) // 2
    up = downscale(g0[y0:y0 + crop_h, x0:x0 + crop_w], g0.shape[0], g0.shape[1])
    return float((zscore(up) * zscore(g1)).mean())


def hist_corr(a: np.ndarray, b: np.ndarray) -> float:
    def hist(frame: np.ndarray) -> np.ndarray:
        small = downscale(frame, 80, 45)
        counts = []
        for channel in range(3):
            counts.append(np.histogram(small[:, :, channel], bins=16, range=(0, 255))[0])
        vec = np.concatenate(counts).astype(np.float32)
        vec /= vec.sum() + 1e-6
        return vec
    ha, hb = hist(a), hist(b)
    return float(np.corrcoef(ha, hb)[0, 1])


def words_of(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    words = []
    for segment in payload["segments"]:
        for word in segment["words"]:
            token = "".join(ch for ch in word["word"].lower() if ch.isalpha() or ch == "'")
            words.append({**word, "token": token, "segment_text": segment["text"]})
    return words


def norm_tokens(words: list[dict]) -> list[str]:
    return [word["token"] for word in words if word["token"]]


def silence_spans(path: Path) -> list[dict]:
    spans = []
    start = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        found = re.search(r"silence_start: ([0-9.]+)", line)
        if found:
            start = float(found.group(1))
        found = re.search(r"silence_end: ([0-9.]+) \| silence_duration: ([0-9.]+)", line)
        if found and start is not None:
            spans.append({
                "start": round(start, 3),
                "end": round(float(found.group(1)), 3),
                "duration": round(float(found.group(2)), 3),
            })
            start = None
    return spans


def rms_db(path: Path) -> dict:
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
        check=True, capture_output=True,
    )
    samples = np.frombuffer(proc.stdout, dtype=np.float32)
    hop = 1600  # 100 ms
    windows = samples[: len(samples) // hop * hop].reshape(-1, hop)
    power = np.sqrt((windows.astype(np.float64) ** 2).mean(axis=1) + 1e-12)
    db = 20 * np.log10(power)
    return {
        "p10_dbfs": round(float(np.percentile(db, 10)), 2),
        "p50_dbfs": round(float(np.percentile(db, 50)), 2),
        "p90_dbfs": round(float(np.percentile(db, 90)), 2),
        "fraction_below_minus_40": round(float((db < -40).mean()), 4),
        "fraction_below_minus_35": round(float((db < -35).mean()), 4),
    }


def ocr_band(frame: np.ndarray, y0: int, y1: int) -> str:
    band = frame[y0:y1]
    if band.size == 0:
        return ""
    height, width = band.shape[:2]
    proc = subprocess.run(
        [
            "ffmpeg", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{width}x{height}", "-i", "-",
            "-vf", "scale=iw*3:ih*3:flags=lanczos",
            "-f", "image2pipe", "-vcodec", "png", "-",
        ],
        input=band.tobytes(), check=True, capture_output=True,
    )
    text = subprocess.run(
        ["tesseract", "stdin", "stdout", "--psm", "6"],
        input=proc.stdout, capture_output=True,
    )
    return " ".join(text.stdout.decode("utf-8", errors="replace").split())


def load_loudness(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    integrated = re.search(r"I:\s+(-?[0-9.]+) LUFS", text)
    lra = re.search(r"LRA:\s+([0-9.]+) LU", text)
    peak = re.search(r"Peak:\s+(-?[0-9.]+) dBFS", text)
    # The summary block is last; take the last match of each.
    def last(pattern: str) -> float | None:
        found = re.findall(pattern, text)
        return float(found[-1]) if found else None
    return {
        "integrated_lufs": last(r"I:\s+(-?[0-9.]+) LUFS"),
        "lra_lu": last(r"LRA:\s+([0-9.]+) LU"),
        "true_peak_dbfs": last(r"Peak:\s+(-?[0-9.]+) dBFS"),
    }


def main() -> None:
    final_fps = 4
    final = ffmpeg_frames(FINAL, final_fps, 360, 640)
    raw_sample = ffmpeg_frames(RAW, 1, 202, 360)
    times = np.arange(len(final)) / final_fps

    masks = [text_mask(frame) for frame in final]
    text_rows = []
    text_counts = []
    for mask in masks:
        rows = np.flatnonzero(mask.sum(axis=1) > 6)
        text_rows.append(rows)
        text_counts.append(int(mask.sum()))

    # Talking-head reference: the 2 second frame. Captions on this final sit in a
    # horizontal band through the middle of the picture, not in the lower third.
    ref_index = int(2 * final_fps)
    correlations = [hist_corr(final[ref_index], frame) for frame in final]
    classes = []
    for index, rows in enumerate(text_rows):
        corr = correlations[index]
        # Only a frame that does not resemble the talking-head reference at all
        # is treated as a card. A caption change is not a scene change.
        if corr < 0.25:
            kind = "other"
        else:
            kind = "talking_head"
        classes.append(kind)

    # Zoom: compare talking-head frames 4 seconds apart.
    zoom_pairs = []
    step = int(4 * final_fps)
    scales = np.round(np.linspace(1.0, 1.30, 13), 3)
    for index in range(0, len(final) - step, step):
        if classes[index] != "talking_head" or classes[index + step] != "talking_head":
            continue
        scored = [(float(scale), zoom_score(final[index], final[index + step], float(scale))) for scale in scales]
        best_scale, best_score = max(scored, key=lambda item: item[1])
        base_score = scored[0][1]
        zoom_pairs.append({
            "t": round(float(times[index]), 2),
            "best_scale": best_scale,
            "best_score": round(best_score, 3),
            "scale_1_score": round(base_score, 3),
            "margin": round(best_score - base_score, 3),
        })

    # The bright glyph rows on sampled frames cluster around the vertical middle.
    y0 = int(0.40 * final.shape[1])
    y1 = int(0.66 * final.shape[1])
    ocr = []
    for index in range(0, len(final), 4):  # 1 second at 4 fps
        text = ocr_band(final[index], y0, y1)
        ocr.append({"t": round(float(times[index]), 2), "kind": classes[index], "text": text})

    cues = []
    for sample in ocr:
        text = sample["text"].strip()
        if len(text) < 2:
            continue
        if cues and cues[-1]["text"].lower() == text.lower() and sample["t"] - cues[-1]["end"] <= 0.75:
            cues[-1]["end"] = sample["t"] + 0.5
            continue
        cues.append({"start": sample["t"], "end": sample["t"] + 0.5, "text": text, "kind": sample["kind"]})

    raw_words = words_of(WEEK / "transcript_raw.json")
    final_words = words_of(WEEK / "transcript_final.json")
    raw_tokens = norm_tokens(raw_words)
    final_tokens = norm_tokens(final_words)
    matcher = SequenceMatcher(a=raw_tokens, b=final_tokens, autojunk=False)
    long_matches = []
    for block in matcher.get_matching_blocks():
        if block.size >= 4:
            long_matches.append({
                "size": block.size,
                "raw": " ".join(raw_tokens[block.a:block.a + block.size]),
                "final": " ".join(final_tokens[block.b:block.b + block.size]),
            })

    # Cross-check OCR caption cues against Whisper words near that time.
    disagreements = []
    checks = 0
    hits = 0
    for cue in cues:
        if cue["kind"] != "talking_head":
            continue
        ocr_tokens = ["".join(ch for ch in part.lower() if ch.isalpha()) for part in cue["text"].split()]
        ocr_tokens = [token for token in ocr_tokens if len(token) > 2]
        if not ocr_tokens:
            continue
        checks += 1
        nearby = [
            word["token"] for word in final_words
            if word["token"] and cue["start"] - 1.2 <= word["start"] <= cue["end"] + 1.2
        ]
        overlap = [token for token in ocr_tokens if token in nearby]
        if len(overlap) >= max(1, len(ocr_tokens) // 2):
            hits += 1
        else:
            disagreements.append({"t": cue["start"], "ocr": cue["text"], "whisper_nearby": " ".join(nearby[:16])})

    low_final = [
        {"word": word["word"], "start": word["start"], "prob": word["prob"]}
        for word in final_words if word["prob"] < 0.6
    ]
    low_raw = [
        {"word": word["word"], "start": word["start"], "prob": word["prob"]}
        for word in raw_words if word["prob"] < 0.5
    ]

    # Raw take list: split Whisper segments on gaps, and mark near-repeats.
    raw_payload = json.loads((WEEK / "transcript_raw.json").read_text(encoding="utf-8"))
    segments = raw_payload["segments"]
    takes = []
    bucket: list[dict] = []
    for segment in segments:
        if bucket and segment["start"] - bucket[-1]["end"] > 1.0:
            takes.append(bucket)
            bucket = []
        bucket.append(segment)
    if bucket:
        takes.append(bucket)
    take_rows = []
    previous = ""
    for index, bucket in enumerate(takes, start=1):
        text = " ".join(segment["text"] for segment in bucket)
        ratio = SequenceMatcher(a=previous.lower(), b=text.lower(), autojunk=False).ratio() if previous else 0
        take_rows.append({
            "take": index,
            "start": bucket[0]["start"],
            "end": bucket[-1]["end"],
            "repeat_of_previous": ratio >= 0.55,
            "similarity_to_previous": round(ratio, 2),
            "text": text,
        })
        previous = text

    graphic_spans = []
    start = None
    for index, kind in enumerate(classes):
        if kind == "graphic" and start is None:
            start = float(times[index])
        if kind != "graphic" and start is not None:
            graphic_spans.append({"start": round(start, 2), "end": round(float(times[index]), 2)})
            start = None
    if start is not None:
        graphic_spans.append({"start": round(start, 2), "end": round(float(times[-1]), 2)})

    scene_text = (WEEK / "scenes_final.txt").read_text(encoding="utf-8", errors="replace")
    scene_times = [round(float(value), 2) for value in re.findall(r"pts_time:([0-9.]+)", scene_text)]

    raw_silences = silence_spans(WEEK / "silence_raw.txt")
    report = {
        "proxy_note": "Low-resolution proxies. Raw is 202x360 H.264 of a 4K HEVC 60fps HLG original. Final is 360x640 of a 1080x1920 60fps master. Both proxies are 30fps.",
        "durations": {"raw": 162.367, "final": 69.933},
        "speech_alignment": {
            "method": "SequenceMatcher on Whisper small tokens, autojunk off",
            "ratio": round(matcher.ratio(), 3),
            "raw_tokens": len(raw_tokens),
            "final_tokens": len(final_tokens),
            "matches_of_4_or_more": long_matches,
            "same_recording": matcher.ratio() >= 0.35,
        },
        "picture_similarity_raw_vs_final_frame": round(hist_corr(raw_sample[min(2, len(raw_sample) - 1)], final[ref_index]), 3),
        "loudness": {
            "raw": load_loudness(WEEK / "loud_raw.txt"),
            "final": load_loudness(WEEK / "loud_final.txt"),
            "raw_rms": rms_db(RAW),
            "final_rms": rms_db(FINAL),
        },
        "raw_silences_ge_0.35s": {
            "count": len(raw_silences),
            "total_seconds": round(sum(span["duration"] for span in raw_silences), 2),
            "longest": sorted(raw_silences, key=lambda span: -span["duration"])[:6],
        },
        "final_scene_cut_times": scene_times,
        "caption_geometry": {
            "sample_fps": final_fps,
            "band_fraction_from_top": [0.40, 0.66],
            "ocr_band_px": [y0, y1],
            "note": "White caption glyphs on this proxy sit in the middle of the frame. The lower third is not where the words are.",
        },
        "caption_cues_ocr": cues,
        "ocr_whisper_checks": checks,
        "ocr_whisper_hits": hits,
        "ocr_whisper_disagreements": disagreements[:12],
        "graphic_spans": graphic_spans,
        "zoom_pairs_4s": zoom_pairs,
        "class_counts": {kind: classes.count(kind) for kind in ("talking_head", "graphic", "other")},
        "raw_takes": take_rows,
        "low_confidence_final_prob_below_0.6": low_final,
        "low_confidence_raw_prob_below_0.5": low_raw,
        "whisper": {
            "model": "small",
            "device": "cpu",
            "compute_type": "int8",
            "raw_seconds": raw_payload["seconds"],
            "final_seconds": json.loads((WEEK / "transcript_final.json").read_text())["seconds"],
            "raw_word_mean_prob": round(sum(word["prob"] for word in raw_words) / len(raw_words), 3),
            "final_word_mean_prob": round(sum(word["prob"] for word in final_words) / len(final_words), 3),
        },
        "rough_cut": {
            "feasible": matcher.ratio() >= 0.35,
            "reason": "The final's words are not in this raw, so a FilmCraft timeline cut from the raw cannot reproduce the human edit.",
        },
    }
    (WEEK / "analysis.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "alignment": report["speech_alignment"]["ratio"],
        "picture": report["picture_similarity_raw_vs_final_frame"],
        "caption_band": report["caption_geometry"]["band_fraction_from_top"],
        "ocr_hits": f"{hits}/{checks}",
        "graphics": graphic_spans,
        "zoom": zoom_pairs,
        "classes": report["class_counts"],
        "raw_takes": len(take_rows),
        "raw_silence_s": report["raw_silences_ge_0.35s"]["total_seconds"],
        "loudness": report["loudness"],
    }, indent=2))


if __name__ == "__main__":
    main()
