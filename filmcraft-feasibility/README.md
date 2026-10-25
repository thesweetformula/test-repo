# FilmCraft feasibility

Can an agent replace a human editor for a short vertical clinic video, using [FilmCraft](https://github.com/storytold/filmcraft) 0.12.0, Whisper, and ffmpeg?

This folder is a reproducible test of the mechanical loop. It is not a production editor. The honest verdict is in [RESULTS.md](RESULTS.md).

Week 48 Video 1 was measured from local proxies that are **not in git**. The raw copy of `IMG_7929.MOV` and the human cut "Why Stress Hits Your Gut" are different recordings, so no rough cut was exported. The measured style is [`config/week48.style.yaml`](config/week48.style.yaml). Nothing here is patient content. Do not drop clinic video into git; `work/`, `incoming/`, and media extensions are gitignored.

## What the pipeline does

1. `espeak-ng` speaks `config/speech.txt` (a line we intend to cut, with silences around it).
2. ffmpeg builds a 1080×1920 H.264 clip: blue field, black grid, yellow center square, that narration.
3. faster-whisper (`small`, int8, CPU) writes word timestamps.
4. FilmCraft's headless CLI imports the clip, keeps the speech we want, drops the cut line and long pauses, animates a scale punch-in, imports a one-word-per-cue SRT, and exports H.264 with captions burned in.
5. ffprobe and a pixel check confirm 1080×1920, H.264 + AAC, a larger yellow square at the end (the zoom), white caption glyphs low in the frame, and about −14 LUFS.

## Run it

Linux x86_64. ffmpeg and ffprobe must already be on `PATH`.

```sh
bash scripts/install.sh          # FilmCraft into ~/.local, Python deps into .venv
export PATH="$HOME/.local/bin:$PATH"
bash scripts/run_e2e.sh
```

`scripts/run_e2e.sh` writes media and JSON under `work/` (not committed). A passing run prints `e2e finished` and leaves `work/verify.json` with `"ok": true`.

Useful knobs:

- `WHISPER_MODEL=base` is faster and, on this espeak clip, wrong. The default is `small`.
- `FILMCRAFT_CLI` if `filmcraft-cli` is not in `~/.local/bin`.
- Cut phrase, frame size, zoom, and caption style live in `config/edit.json`.

## Layout

| Path | Role |
| --- | --- |
| `scripts/install.sh` | FilmCraft 0.12.0 tarball, espeak-ng, faster-whisper |
| `scripts/run_e2e.sh` | Synthetic clip through export and the codec/GUI probes |
| `scripts/make_synthetic.sh` | Grid clip + narration |
| `scripts/transcribe.py` | Word timestamps. Patches a PyAV 19 incompatibility |
| `scripts/edit.py` | FilmCraft cut, zoom, captions, export |
| `scripts/verify.py` | ffprobe, zoom, caption, loudness checks |
| `scripts/mcp_smoke.py` | Headless MCP: create a 1080×1920 sequence and import |
| `scripts/probe_codecs.py` | ffmpeg-made HEVC `.MOV`, 8-bit and 10-bit |
| `scripts/check_gui.sh` | Desktop binary. Expected to fail on a VM with no GPU |
| `scripts/transcribe_week48.py` | Whisper on `work/week48/raw.mp4` and `final.mp4`. Default model is `small` |
| `scripts/analyze_week48.py` | Alignment, loudness, caption band, scene cuts. Writes `work/week48/analysis.json`. Does not export |
| `config/week48.style.yaml` | Style measured from the human final, and the reason there is no rough cut |
| `config/STYLE_SPEC.md` | Short pointer at that YAML |

## Week 48 proxies

Put the low-resolution raw and the human final at `work/week48/raw.mp4` and `work/week48/final.mp4`. They stay gitignored. Do not upload them.

```sh
.venv/bin/python scripts/transcribe_week48.py          # small, the transcript
WHISPER_MODEL=medium .venv/bin/python scripts/transcribe_week48.py
.venv/bin/python scripts/analyze_week48.py
```

`analyze_week48.py` reads the `small` transcripts. It refuses a rough cut when the token overlap is under 0.35. On these two files the overlap is 0.05, and no FilmCraft export was made. The comparison is in [RESULTS.md](RESULTS.md).
