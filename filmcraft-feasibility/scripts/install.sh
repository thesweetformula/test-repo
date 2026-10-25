#!/usr/bin/env bash
# Install the tools this feasibility pipeline needs. Safe to re-run.
# FilmCraft goes to ~/.local (no sudo). Python packages go to .venv in this folder.
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)"
VERSION="0.12.0"
TARBALL="filmcraft-${VERSION}-linux-x86_64.tar.gz"
URL="https://github.com/storytold/filmcraft/releases/download/v${VERSION}/${TARBALL}"
SHA256="ddff0a2ec0d89e5e9e65644ed724b5b79959600b1602fd4ea6653b5a54bf88fd"
PREFIX="${HOME}/.local"

if [[ "$(uname -m)" != "x86_64" ]]; then
  echo "This script downloads the linux-x86_64 release. This machine is $(uname -m)." >&2
  exit 1
fi

if ! command -v ffmpeg >/dev/null || ! command -v ffprobe >/dev/null; then
  echo "ffmpeg and ffprobe are required (Ubuntu: sudo apt-get install ffmpeg)." >&2
  exit 1
fi

sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
  espeak-ng espeak-ng-data python3 python3-venv python3-pip time ca-certificates curl

if ! "${PREFIX}/bin/filmcraft-cli" --version 2>/dev/null | grep -q "${VERSION}"; then
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  curl -fL --retry 3 -o "${tmp}/${TARBALL}" "$URL"
  echo "${SHA256}  ${tmp}/${TARBALL}" | sha256sum -c -
  tar -xzf "${tmp}/${TARBALL}" -C "$tmp"
  "${tmp}/filmcraft-${VERSION}-linux-x86_64/install.sh" --prefix "$PREFIX"
fi

"${PREFIX}/bin/filmcraft-cli" --version
"${PREFIX}/bin/filmcraft" --version

python3 -m venv "${ROOT}/.venv"
"${ROOT}/.venv/bin/pip" install -U pip
"${ROOT}/.venv/bin/pip" install -r "${ROOT}/requirements.txt"
"${ROOT}/.venv/bin/python" -c 'import faster_whisper; print("faster-whisper", faster_whisper.__version__)'

echo "Add ${PREFIX}/bin to PATH if it is not already there."
echo "Installed. Desktop FilmCraft still needs a display and a GPU surface; the CLI does not."
