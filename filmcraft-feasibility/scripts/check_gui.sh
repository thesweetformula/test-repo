#!/usr/bin/env bash
# Record whether the desktop binary can open. The CLI path does not use this.
set +e
ROOT="$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)"
WORK="${ROOT}/work"
mkdir -p "$WORK"
APP="${HOME}/.local/bin/filmcraft"
OUT="${WORK}/gui-check.txt"
{
  echo "version: $("$APP" --version 2>&1)"
  echo "nproc: $(nproc)"
  echo "no_dri: $(ls /dev/dri 2>/dev/null || echo none)"
  echo
  echo "===== no DISPLAY, --graphics software ====="
  rm -rf /tmp/fc-gui-nodisp
  mkdir -p /tmp/fc-gui-nodisp
  env -u DISPLAY -u WAYLAND_DISPLAY timeout --signal=TERM 8 \
    "$APP" --empty --graphics software --data-dir /tmp/fc-gui-nodisp --no-recover \
    >/tmp/fc-gui-nodisp/out.txt 2>/tmp/fc-gui-nodisp/err.txt
  echo "exit: $?"
  cat /tmp/fc-gui-nodisp/err.txt
  echo
  echo "===== DISPLAY=${DISPLAY:-unset}, --graphics software ====="
  rm -rf /tmp/fc-gui-disp
  mkdir -p /tmp/fc-gui-disp
  timeout --signal=TERM 8 \
    "$APP" --empty --graphics software --data-dir /tmp/fc-gui-disp --no-recover \
    >/tmp/fc-gui-disp/out.txt 2>/tmp/fc-gui-disp/err.txt
  echo "exit: $?"
  cat /tmp/fc-gui-disp/err.txt
} >"$OUT" 2>&1
echo "wrote $OUT"
# GUI failure is a finding, not a pipeline failure.
exit 0
