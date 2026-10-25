"""Shared paths and headless FilmCraft CLI helpers."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"
CONFIG = ROOT / "config"
FC = os.environ.get("FILMCRAFT_CLI", str(Path.home() / ".local" / "bin" / "filmcraft-cli"))
TICKS_PER_SECOND = 254_016_000_000


def headless_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("DISPLAY", None)
    env.pop("WAYLAND_DISPLAY", None)
    env.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    return env


def ensure_work() -> Path:
    WORK.mkdir(parents=True, exist_ok=True)
    return WORK


def ticks_per_frame(fps: int) -> int:
    if TICKS_PER_SECOND % fps != 0:
        raise ValueError(f"{fps} fps does not divide FilmCraft's tick rate")
    return TICKS_PER_SECOND // fps


def run_cli(args: list[str], *, log_name: str = "cli.log") -> subprocess.CompletedProcess[str]:
    ensure_work()
    proc = subprocess.run(
        [FC, *args],
        capture_output=True,
        text=True,
        env=headless_env(),
    )
    with (WORK / log_name).open("a", encoding="utf-8") as fh:
        fh.write("$ " + " ".join(args) + "\n")
        fh.write(proc.stdout)
        if proc.stdout and not proc.stdout.endswith("\n"):
            fh.write("\n")
        if proc.stderr:
            fh.write(proc.stderr)
            if not proc.stderr.endswith("\n"):
                fh.write("\n")
        fh.write(f"[exit {proc.returncode}]\n\n")
    return proc


def run_steps(steps: list[dict], *, project: Path | None = None, save_as: Path | None = None) -> list[dict]:
    ensure_work()
    jsonl = WORK / "_steps.jsonl"
    jsonl.write_text("".join(json.dumps(step) + "\n" for step in steps), encoding="utf-8")
    args: list[str] = []
    if save_as is not None:
        args += ["--save-as", str(save_as)]
    elif project is not None:
        args += ["--project", str(project), "--save"]
    else:
        raise ValueError("project or save_as is required")
    args += ["run", str(jsonl)]
    proc = run_cli(args)
    lines = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    failed = [line for line in lines if not line.get("ok")]
    if proc.returncode != 0 or failed or len(lines) != len(steps):
        detail = json.dumps(failed or lines, indent=2)
        raise RuntimeError(
            f"filmcraft-cli run failed (exit {proc.returncode})\n{detail}\nstderr:\n{proc.stderr}"
        )
    return lines


def parse_json_stdout(proc: subprocess.CompletedProcess[str]) -> dict:
    if proc.returncode != 0:
        raise RuntimeError(f"filmcraft-cli failed ({proc.returncode}): {proc.stderr}\n{proc.stdout}")
    return json.loads(proc.stdout)
