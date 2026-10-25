#!/usr/bin/env python3
"""See whether FilmCraft's own demuxer reads short HEVC .MOV files, including 10-bit.

This is not an iPhone file. It answers the codec question only.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from common import FC, WORK, ensure_work, headless_env, parse_json_stdout, run_cli, run_steps


def ffmpeg(args: list[str]) -> None:
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args], check=True)


def render_import(path: Path, width: int, height: int, dest: Path, *, audio: bool) -> dict:
    project = dest.with_suffix(".fcproj")
    if project.exists():
        project.unlink()
    created = run_steps(
        [
            {
                "id": "file.newSequence",
                "params": {
                    "name": path.stem,
                    "width": width,
                    "height": height,
                    "fps": 30,
                    "video": 1,
                    "audio": 1,
                },
            },
            {"id": "file.import", "params": {"paths": [str(path.resolve())]}},
        ],
        save_as=project,
    )
    item = created[1]["result"]["items"][0]
    run_steps(
        [
            {
                "id": "timeline.place",
                "params": {"item": item, "frame": 0, "insert": False, "video": True, "audio": audio},
            }
        ],
        project=project,
    )
    proc = run_cli(
        ["--project", str(project), "render", "--seconds", "0.1", "--out", str(dest)]
    )
    if proc.returncode != 0 or not dest.exists() or dest.stat().st_size < 1000:
        raise RuntimeError(f"render failed for {path}: {proc.stderr}")
    return {"item": item, "png_bytes": dest.stat().st_size, "render_stdout": proc.stdout.strip()}


def main() -> None:
    ensure_work()
    codec_dir = WORK / "codec-probe"
    codec_dir.mkdir(exist_ok=True)
    hevc = codec_dir / "sample_hevc.MOV"
    hevc10 = codec_dir / "sample_hevc10.MOV"
    ffmpeg(
        [
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=720x1280:rate=30:duration=0.5",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000:duration=0.5",
            "-c:v",
            "libx265",
            "-tag:v",
            "hvc1",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(hevc),
        ]
    )
    ffmpeg(
        [
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=640x360:rate=30:duration=0.4",
            "-c:v",
            "libx265",
            "-tag:v",
            "hvc1",
            "-pix_fmt",
            "yuv420p10le",
            "-an",
            str(hevc10),
        ]
    )
    report = {"filmcraft": subprocess.check_output([FC, "--version"], text=True, env=headless_env()).strip()}
    samples = (
        ("hevc_8bit_mov", hevc, (720, 1280), True),
        ("hevc_10bit_mov", hevc10, (640, 360), False),
    )
    for label, path, size, audio in samples:
        probe = parse_json_stdout(run_cli(["probe", str(path)]))
        rendered = render_import(path, size[0], size[1], codec_dir / f"{label}.png", audio=audio)
        video = probe["video"]
        report[label] = {
            "container": probe["container"],
            "codec": video["codec"],
            "pixel_format": video["pixel_format"],
            "width": video["width"],
            "height": video["height"],
            "rotation_fields": [key for key in video if "rot" in key.lower() or "orient" in key.lower()],
            "render": rendered,
        }
    report["notes"] = [
        "Files are ffmpeg libx265 in a QuickTime .MOV with the hvc1 tag, not iPhone camera originals.",
        "FilmCraft probe JSON has no rotation field. ffmpeg 6.1.1 on this VM did not write a QuickTime display matrix via -metadata:s:v rotate=90, so portrait-matrix handling is untested.",
    ]
    (WORK / "codec-probe.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
