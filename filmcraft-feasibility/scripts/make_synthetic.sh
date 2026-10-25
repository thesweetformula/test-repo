#!/usr/bin/env bash
# Build a 9:16 H.264 clip: static grid + yellow center box + espeak narration.
# The grid and box are there so a later frame compare can see a zoom.
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)"
WORK="${ROOT}/work"
mkdir -p "$WORK"

SPEECH="${ROOT}/config/speech.txt"
WAV="${WORK}/speech.wav"
OUT="${WORK}/synthetic.mp4"

espeak-ng -v en-us -s 132 -g 6 -w "$WAV" -f "$SPEECH"
DUR="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$WAV")"

ffmpeg -y -hide_banner -loglevel error \
  -f lavfi -i "color=c=0x3a7ca5:size=1080x1920:rate=30:duration=${DUR},drawgrid=width=90:height=90:thickness=4:color=black,drawbox=x=440:y=860:w=200:h=200:color=yellow:t=fill" \
  -i "$WAV" \
  -c:v libx264 -pix_fmt yuv420p -preset veryfast -crf 18 \
  -c:a aac -ac 2 -ar 48000 -b:a 160k \
  -shortest -movflags +faststart \
  "$OUT"

echo "synthetic ${OUT}"
ffprobe -hide_banner -v error -show_entries format=duration:stream=codec_name,width,height,avg_frame_rate -of default=nw=1 "$OUT"
