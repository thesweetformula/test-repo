#!/usr/bin/env python3
"""Prove filmcraft-cli mcp drives a headless project over stdio. No window, no display."""

from __future__ import annotations

import json
import os
import select
import subprocess
from pathlib import Path

from common import FC, WORK, ensure_work, headless_env


def main() -> None:
    ensure_work()
    media = WORK / "synthetic.mp4"
    if not media.exists():
        raise SystemExit(f"missing {media}")
    proc = subprocess.Popen(
        [FC, "mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=headless_env(),
        bufsize=1,
    )

    def send(message: dict) -> None:
        assert proc.stdin is not None
        proc.stdin.write(json.dumps(message) + "\n")
        proc.stdin.flush()

    def read(timeout: float = 30) -> dict:
        assert proc.stdout is not None
        ready, _, _ = select.select([proc.stdout], [], [], timeout)
        if not ready:
            err = proc.stderr.read() if proc.stderr and proc.poll() is not None else ""
            raise TimeoutError(f"MCP timed out poll={proc.poll()} stderr={err[:600]}")
        line = proc.stdout.readline()
        if not line:
            err = proc.stderr.read() if proc.stderr else ""
            raise RuntimeError(f"MCP closed stdout stderr={err[:600]}")
        return json.loads(line)

    try:
        send(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "filmcraft-feasibility", "version": "0.1"},
                },
            }
        )
        init = read()
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tools = read()
        names = [tool["name"] for tool in tools["result"]["tools"]]
        send(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "command_run",
                    "arguments": {
                        "id": "file.newSequence",
                        "params": {"name": "MCP", "width": 1080, "height": 1920, "fps": 30, "video": 1, "audio": 1},
                    },
                },
            }
        )
        created = read()
        send(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "media_import", "arguments": {"paths": [str(media.resolve())]}},
            }
        )
        imported = read()
        send(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {"name": "sequence_inspect", "arguments": {}},
            }
        )
        inspected = read()
        result = {
            "server": init.get("result", {}).get("serverInfo"),
            "protocol": init.get("result", {}).get("protocolVersion"),
            "tools": names,
            "new_sequence_is_error": created.get("result", {}).get("isError"),
            "import_is_error": imported.get("result", {}).get("isError"),
            "import_text": (imported.get("result", {}).get("content") or [{}])[0].get("text", "")[:500],
            "sequence_width": None,
            "display_in_env": "DISPLAY" in os.environ and bool(os.environ.get("DISPLAY")),
        }
        # The child env has DISPLAY removed. Record that explicitly.
        result["child_display_removed"] = True
        text = (inspected.get("result", {}).get("content") or [{}])[0].get("text", "")
        if text:
            sequence = json.loads(text)
            result["sequence_width"] = sequence.get("settings", {}).get("width")
            result["sequence_height"] = sequence.get("settings", {}).get("height")
        result["ok"] = (
            result["server"] == {"name": "filmcraft", "version": "0.12.0"}
            and result["new_sequence_is_error"] is False
            and result["import_is_error"] is False
            and result["sequence_width"] == 1080
            and result["sequence_height"] == 1920
            and "media_import" in names
            and "command_run" in names
        )
        (WORK / "mcp-smoke.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        if not result["ok"]:
            raise SystemExit(1)
    finally:
        if proc.stdin:
            proc.stdin.close()
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
