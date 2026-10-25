#!/usr/bin/env bash
# Synthetic end-to-end: speech, transcribe, FilmCraft edit, export, verify.
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p work
export PATH="${HOME}/.local/bin:${PATH}"
export HF_HUB_DISABLE_TELEMETRY=1
PY="${ROOT}/.venv/bin/python"
LOG="${ROOT}/work/e2e.log"
: >"$LOG"

step() {
  echo "===== $* =====" | tee -a "$LOG"
  /usr/bin/time -v "$@" >>"$LOG" 2>&1
}

step bash scripts/make_synthetic.sh
step "$PY" scripts/transcribe.py
step "$PY" scripts/edit.py
step "$PY" scripts/verify.py
step "$PY" scripts/mcp_smoke.py
step "$PY" scripts/probe_codecs.py
bash scripts/check_gui.sh
echo "e2e finished" | tee -a "$LOG"
