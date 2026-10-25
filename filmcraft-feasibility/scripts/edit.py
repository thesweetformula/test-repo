#!/usr/bin/env python3
"""Cut the synthetic clip in FilmCraft, zoom it, burn word captions, export 1080x1920."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from common import CONFIG, FC, WORK, ensure_work, headless_env, parse_json_stdout, run_cli, run_steps, ticks_per_frame


def norm(word: str) -> str:
    return "".join(ch for ch in word.lower() if ch.isalpha())


def flatten_words(transcript: dict) -> list[dict]:
    words = []
    for seg in transcript["segments"]:
        words.extend(seg["words"])
    return words


def find_phrase(words: list[dict], phrase: str) -> tuple[int, int]:
    target = [norm(part) for part in phrase.split()]
    if not target:
        raise RuntimeError("drop_phrase is empty")
    last = len(words) - len(target) + 1
    for start in range(max(0, last)):
        window = [norm(words[start + offset]["word"]) for offset in range(len(target))]
        if window == target:
            return start, start + len(target) - 1
    heard = " ".join(word["word"] for word in words)
    raise RuntimeError(f"could not find drop phrase {phrase!r} in transcript: {heard}")


def keep_ranges(words: list[dict], drop_segments: set[int], cfg: dict, media_duration: float) -> list[tuple[float, float]]:
    kept = [word for word in words if word["segment"] not in drop_segments]
    if not kept:
        raise RuntimeError("every word was dropped")
    max_gap = float(cfg["max_gap_seconds"])
    handle = float(cfg["handle_seconds"])
    clusters: list[list[dict]] = [[kept[0]]]
    for word in kept[1:]:
        if word["start"] - clusters[-1][-1]["end"] > max_gap:
            clusters.append([word])
        else:
            clusters[-1].append(word)
    ranges: list[tuple[float, float]] = []
    for cluster in clusters:
        start = max(0.0, cluster[0]["start"] - handle)
        end = min(media_duration, cluster[-1]["end"] + handle)
        if end - start >= 0.05:
            ranges.append((start, end))
    return ranges


def srt_timestamp(seconds: float) -> str:
    ms = max(0, int(round(seconds * 1000)))
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def locate_source_time(seconds: float, placements: list[dict], fps: int) -> tuple[int, float] | None:
    frame = seconds * fps
    for index, place in enumerate(placements):
        src_end = place["src_frame_in"] + place["src_frames"]
        if place["src_frame_in"] - 0.51 <= frame <= src_end + 0.51:
            return index, (place["tl_frame"] + (frame - place["src_frame_in"])) / fps
    return None


def write_word_srt(words: list[dict], drop_segments: set[int], placements: list[dict], fps: int, path: Path) -> int:
    cues = []
    for word in words:
        if word["segment"] in drop_segments or not word["word"]:
            continue
        start_at = locate_source_time(word["start"], placements, fps)
        end_at = locate_source_time(word["end"], placements, fps)
        if start_at is None or end_at is None or start_at[0] != end_at[0]:
            continue
        start, end = start_at[1], end_at[1]
        if end < start:
            start, end = end, start
        if end - start < 0.08:
            end = start + 0.08
        cues.append((start, end, word["word"]))
    lines = []
    for index, (start, end, text) in enumerate(cues, start=1):
        lines.append(str(index))
        lines.append(f"{srt_timestamp(start)} --> {srt_timestamp(end)}")
        lines.append(text)
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return len(cues)


def main() -> None:
    ensure_work()
    cfg = json.loads((CONFIG / "edit.json").read_text(encoding="utf-8"))
    transcript = json.loads((WORK / "transcript.json").read_text(encoding="utf-8"))
    media = (WORK / "synthetic.mp4").resolve()
    project = (WORK / "edit.fcproj").resolve()
    srt_path = (WORK / "captions.srt").resolve()
    export_path = (WORK / "export.mp4").resolve()
    fps = int(cfg["fps"])
    tpf = ticks_per_frame(fps)

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(media)],
        check=True,
        capture_output=True,
        text=True,
    )
    media_duration = float(probe.stdout.strip())
    words = flatten_words(transcript)
    phrase_start, phrase_end = find_phrase(words, cfg["drop_phrase"])
    drop_segments = {words[index]["segment"] for index in range(phrase_start, phrase_end + 1)}
    ranges = keep_ranges(words, drop_segments, cfg, media_duration)

    placements = []
    timeline_frame = 0
    for src_start, src_end in ranges:
        src_in = int(round(src_start * fps))
        src_out = int(round(src_end * fps))
        if src_out <= src_in:
            continue
        placements.append(
            {
                "src_start": src_start,
                "src_end": src_end,
                "src_frame_in": src_in,
                "src_frames": src_out - src_in,
                "tl_frame": timeline_frame,
            }
        )
        timeline_frame += src_out - src_in
    if timeline_frame <= 0:
        raise RuntimeError("timeline is empty after cuts")

    if project.exists():
        project.unlink()
    created = run_steps(
        [
            {
                "id": "file.newSequence",
                "params": {
                    "name": "Synthetic vertical",
                    "width": cfg["width"],
                    "height": cfg["height"],
                    "fps": fps,
                    "sampleRate": cfg["sample_rate"],
                    "video": 1,
                    "audio": 1,
                },
            },
            {"id": "file.import", "params": {"paths": [str(media)]}},
        ],
        save_as=project,
    )
    item_id = created[1]["result"]["items"][0]
    place_steps = []
    for place in placements:
        place_steps.append(
            {
                "id": "timeline.place",
                "params": {
                    "item": item_id,
                    "track": "V1",
                    "audioTrack": "A1",
                    "frame": place["tl_frame"],
                    "insert": False,
                    "sourceIn": place["src_frame_in"] * tpf,
                    "duration": place["src_frames"] * tpf,
                    "video": True,
                    "audio": True,
                },
            }
        )
    run_steps(place_steps, project=project)

    sequence = parse_json_stdout(run_cli(["--project", str(project), "inspect", "sequence"]))
    video_clips = sorted(sequence["video"][0]["items"], key=lambda item: item["start"])
    total_ticks = timeline_frame * tpf
    zoom_steps = []
    for clip in video_clips:
        start = int(clip["start"])
        end = int(clip["end"])
        if end <= start:
            continue
        span = max(total_ticks, 1)
        scale0 = cfg["zoom_start_percent"] + (cfg["zoom_end_percent"] - cfg["zoom_start_percent"]) * (start / span)
        scale1 = cfg["zoom_start_percent"] + (cfg["zoom_end_percent"] - cfg["zoom_start_percent"]) * (end / span)
        for when, scale in ((start, scale0), (end, scale1)):
            zoom_steps.append(
                {
                    "id": "effects.setParam",
                    "params": {
                        "clip": clip["clip"],
                        "effect": "motion",
                        "param": "scale",
                        "value": round(scale, 3),
                        "keyframe": True,
                        "time": when,
                    },
                }
            )
        zoom_steps.append(
            {
                "id": "effects.setInterpolation",
                "params": {
                    "clip": clip["clip"],
                    "effect": "motion",
                    "param": "scale",
                    "mediaTime": start,
                    "interpolation": "easeOut",
                },
            }
        )
    # Interpolation is optional. A failure must not throw away the linear zoom.
    jsonl = WORK / "_zoom.jsonl"
    jsonl.write_text("".join(json.dumps(step) + "\n" for step in zoom_steps), encoding="utf-8")
    zoom_proc = run_cli(["--project", str(project), "--save", "--keep-going", "run", str(jsonl)])
    zoom_lines = [json.loads(line) for line in zoom_proc.stdout.splitlines() if line.strip()]
    zoom_failures = [line for line in zoom_lines if not line.get("ok")]

    cue_count = write_word_srt(words, drop_segments, placements, fps, srt_path)
    style = {"track": "C1", **cfg["caption_style"]}
    caption_lines = run_steps(
        [
            {"id": "captions.import", "params": {"path": str(srt_path), "name": "Words"}},
            {"id": "captions.setStyle", "params": style},
        ],
        project=project,
    )

    export_seconds = timeline_frame / fps
    # `loudnessLufs` is accepted by `exec file.exportMedia` but rejected inside
    # `export --settings`. The preset stores it under effects.loudness.
    settings = {
        "burnCaptions": True,
        "hardwareEncoding": "off",
        "effects": {
            "loudness": {
                "enabled": True,
                "target_lufs": cfg["loudness_lufs"],
                "true_peak_dbtp": -1.5,
            }
        },
    }
    export_meta = export_with_fallback(project, export_path, cfg["export_preset"], settings, export_seconds)

    report = {
        "media": str(media),
        "media_duration": media_duration,
        "drop_phrase": cfg["drop_phrase"],
        "dropped_segments": sorted(drop_segments),
        "dropped_text": [
            seg["text"] for seg in transcript["segments"] if seg["segment"] in drop_segments
        ],
        "kept_transcript_text": [
            seg["text"] for seg in transcript["segments"] if seg["segment"] not in drop_segments
        ],
        "ranges": placements,
        "timeline_frames": timeline_frame,
        "timeline_seconds": export_seconds,
        "sequence_duration_frames_after_place": sequence["durationFrames"],
        "caption_cues": cue_count,
        "caption_import": caption_lines[0]["result"],
        "zoom_failures": zoom_failures,
        "video_clips": [
            {"clip": clip["clip"], "startFrame": clip["startFrame"], "endFrame": clip["endFrame"]}
            for clip in video_clips
        ],
        "export": export_meta,
    }
    (WORK / "edit-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"timeline {export_seconds:.2f}s ({timeline_frame} frames) "
        f"cues {cue_count} export {export_meta.get('path')}"
    )


def export_with_fallback(project: Path, export_path: Path, preset: str, settings: dict, end_seconds: float) -> dict:
    without_loudness = {key: value for key, value in settings.items() if key != "effects"}
    attempts = [settings, without_loudness]
    errors = []
    for attempt in attempts:
        if export_path.exists():
            export_path.unlink()
        started = time.perf_counter()
        proc = subprocess.run(
            [
                "/usr/bin/time",
                "-v",
                FC,
                "--project",
                str(project),
                "export",
                str(export_path),
                "--preset",
                preset,
                "--start",
                "0",
                "--end",
                f"{end_seconds:.6f}",
                "--settings",
                json.dumps(attempt),
            ],
            capture_output=True,
            text=True,
            env=headless_env(),
        )
        wall = time.perf_counter() - started
        (WORK / "cli.log").open("a", encoding="utf-8").write(proc.stdout + "\n" + proc.stderr + "\n")
        if proc.returncode == 0 and export_path.exists():
            payload = json.loads(proc.stdout)
            rss = None
            for line in proc.stderr.splitlines():
                if "Maximum resident set size" in line:
                    rss = int(line.split(":")[-1].strip())
            payload["wall_seconds"] = round(wall, 3)
            payload["max_rss_kb"] = rss
            payload["settings"] = attempt
            payload["loudness_applied"] = "effects" in attempt
            return payload
        errors.append(proc.stderr.strip() or proc.stdout.strip())
    raise RuntimeError("export failed:\n" + "\n---\n".join(errors))


if __name__ == "__main__":
    main()
