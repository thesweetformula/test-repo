# Results

**An agent can drive the mechanical edit. It cannot replace the human editor yet.**

On this VM, FilmCraft 0.12.0's command-line tool, with no window and no GPU, took a 15-second synthetic 9:16 clip, dropped a sentence and the long pauses, ramped a zoom with linear scale keyframes, burned one-word captions, loudness-normalized to about −14 LUFS, and wrote a 1080×1920 H.264 MP4 that ffprobe can play. That is the part a human editor does with the mouse.

It is not the part that decides what the video is. The test clip is a grid and a text-to-speech voice, not Dr Froomes on an iPhone. Whisper `small` transcribed that voice well and still invented the word "Sint". The desktop app does not open here. The real raw and the human final were not available, so there is no style match and no quality comparison against the clinic cut.

Use this as a first-pass assembler that a person reviews. Do not put it on the weekly publish path.

## What was actually produced

Spoken script (`config/speech.txt`):

> Stress hits your gut before you notice it.
> Please cut this whole sentence from the edit.
> Your nervous system and digestion share the same wiring.

Whisper `small` (int8, CPU, word timestamps) heard:

> Stress hits your gut before you notice it.
> Sint, please cut this whole sentence from the edit.
> Sint, your nervous system and digestion share the same wiring.

The pipeline dropped the whole middle segment because it contained the configured phrase. The export is **9.07 seconds** (272 frames at 30 fps) from **14.98 seconds** of source. The burned captions are the first sentence, then a phantom **"Sint,"**, then the last sentence. The sentence we asked to cut is gone, and so is most of the silence around it.

`work/verify.json` from this run: `"ok": true`.

| Check | Measured |
| --- | --- |
| Container | MP4, encoder tag `FilmCraft 0.12.0` |
| Video | H.264, yuv420p, 1080×1920, 30 fps, about 12.2 Mbps |
| Audio | AAC, stereo, 48 kHz |
| Duration | 9.10 s in the file, 9.07 s of timeline |
| File size | 13.9 MB |
| Zoom | Yellow 200×200 square is exactly 40,000 px at 0.25 s and 53,869 px near the end (about 1.16× linear, in line with a ramp toward 118%) |
| Captions | White glyphs, none in the top 12% of the frame. Their row center sits at 80% of the height (lower fifth). First sampled word is "Stress" |
| Loudness | −14.1 LUFS integrated (target −14, true-peak target −1.5 dBTP) |

I looked at extracted frames. Early in the clip the grid is small and the yellow square is 200 px. Near the end the grid lines are thicker and the square is larger, which is the punch-in. The caption sits in a translucent dark bar low in the frame, one word at a time. That is not the same as a line of words with the current word highlighted. FilmCraft's caption track has one style for the whole cue, so word-by-word here means a new cue per word.

## Install, version, machine

FilmCraft **0.12.0** (release 2026-10-23). There is a prebuilt Linux tarball. No source build.

```sh
curl -fL -o filmcraft-0.12.0-linux-x86_64.tar.gz \
  https://github.com/storytold/filmcraft/releases/download/v0.12.0/filmcraft-0.12.0-linux-x86_64.tar.gz
echo "ddff0a2ec0d89e5e9e65644ed724b5b79959600b1602fd4ea6653b5a54bf88fd  filmcraft-0.12.0-linux-x86_64.tar.gz" | sha256sum -c -
tar -xzf filmcraft-0.12.0-linux-x86_64.tar.gz
./filmcraft-0.12.0-linux-x86_64/install.sh --prefix "$HOME/.local"
```

The tarball is 69,907,641 bytes. `filmcraft-cli --version` and `filmcraft --version` both print `0.12.0`. Install took 0.16 s and 7 MB RSS. The binaries are 79 MB and 60 MB, dynamically linked only to libgcc, libm, and libc. `scripts/install.sh` repeats this and also installs espeak-ng and the Python venv.

Other tools:

- ffmpeg **6.1.1** was already on the image (`ffmpeg version 6.1.1-3ubuntu5`). Used for the synthetic clip, ffprobe, and the loudness meter. FilmCraft does not shell out to ffmpeg to decode or encode.
- espeak-ng **1.51** from apt.
- faster-whisper **1.2.1** in `.venv`, CPU int8. `pip install` peaked at 106 MB RSS.

Machine: Ubuntu 24.04.5, kernel 6.12.94+, **4 vCPU** Intel Xeon (family 6, model 207, AVX-512). No `/dev/dri`, no NVIDIA driver. `free` showed 15 GiB with a large hypervisor balloon, so that number is not the RAM the process could actually touch. The export itself peaked at **1.31 GB RSS**.

`filmcraft-cli commands --json` lists **701** commands on this build.

## Headless, GPU, display

The CLI and the MCP server do not need a display or a GPU. `scripts/common.py` strips `DISPLAY` and `WAYLAND_DISPLAY` before every CLI call. Rendering and export ran that way, on the CPU path (`hardwareEncoding: off`). One 1080×1920 preview frame earlier in the session took about 0.2 s and 290 MB RSS. The 272-frame export ran at **16.6 frames/s**, **16.5 s** wall, **360% CPU**, **1.31 GB** RSS.

The desktop binary does not run here.

- With no `DISPLAY`: it exits immediately. winit says neither Wayland nor X11 is set. FilmCraft's own log also says hardware decode is unavailable (no VA-API render node, no NVDEC).
- With `DISPLAY=:1` and `--graphics software`: after installing `libxkbcommon-x11-0` (the first launch panicked on a missing `libxkbcommon-x11.so`), it still exits. wgpu: `Failed to create surface for any enabled backend`. Software graphics mode did not produce a CPU window on this VM.

MCP works headless. `scripts/mcp_smoke.py` spoke JSON-RPC 2024-11-05 to `filmcraft-cli mcp`, got server `filmcraft` 0.12.0, created a 1080×1920 sequence with `command_run`, and imported the synthetic file with `media_import`. The server also advertises UI tools (`ui_click`, `ui_screenshot`, and the rest). Those need the desktop app, which is the bridge mode (`filmcraft --control`), and that app does not start here. The edit itself does not need them.

## Commands that worked

Happy path, all through `filmcraft-cli` with `--save` / `--save-as`, project in `work/` (gitignored):

| Command | What it did |
| --- | --- |
| `file.newSequence` | 1080×1920, 30 fps, 48 kHz, one video and one audio track. Inspect reports preset `1080x1920 30`. |
| `file.import` | Absolute path. Returns item ids. Those ids are not stable if the track layout changes, so the script reads them. |
| `timeline.place` | `frame`, `sourceIn` and `duration` in ticks (254,016,000,000 per second). Places picture and sound together. This is how the cut is made: each kept range is a placement, back to back. |
| `effects.setParam` | `effect: "motion"`, `param: "scale"`, `keyframe: true`. Scale is a percent. 100 fills a matching frame. A keyframe at each clip boundary ramps 100 → 118 across the timeline. |
| `captions.import` | SRT, 18 cues, no warnings. |
| `captions.setStyle` | Inter, 68 px, white, black background at about 70% opacity, center, anchor bottom, margin 0.16 of frame height. |
| `export` | Preset **`Social Vertical 1080×1920`** (the multiply sign is part of the name). `--settings` merges `burnCaptions`, `hardwareEncoding`, and `effects.loudness`. |

MCP equivalents used in the smoke test: `command_run`, `media_import`, `sequence_inspect`. `project_inspect` also answered during an earlier manual session.

Codec probe (`scripts/probe_codecs.py`): `probe`, then import, place, and `render` of a frame.

## What failed, and the workaround

**Razor plus ripple is a footgun.** `timeline.razor` with `seconds=1` and `track=V1` cuts only that track. `edit.rippleDelete` of the video piece then fails: "this edit would break sync: A1 is sync-locked". Razor both V1 and A1, then ripple-delete both pieces, and the clips do disappear. The sequence duration does **not**. After deleting the tail, clips ended at frame 30 and `durationFrames` stayed 60. `sequence.closeGap` returned "nothing to do". The export included a second of black. Workaround that did shorten it: `markers.markIn` / `markers.markOut` and `sequence.extract` on that tail. A middle-of-clip extract also closed the gap (a 4 s clip with 1 s extracted came out at 89 frames rather than 90). The pipeline does not use razor. It places only the source ranges it wants, and the sequence length matched the placements (272 frames).

**`edit.undo` does not survive a new CLI process.** Each invocation loads the saved project with an empty undo stack.

**`--settings` is picky.**

- `"audio": true` is rejected: it expects an audio object, not a boolean. Omit it. The preset already includes AAC at 320 kbps.
- `"loudnessLufs": -14` is rejected as an unknown key ("see export.presets.get"). The same number **is** accepted as a direct `exec file.exportMedia loudnessLufs=-14` parameter, and as nested settings:

```json
{"effects": {"loudness": {"enabled": true, "target_lufs": -14, "true_peak_dbtp": -1.5}}}
```

Without loudness, this espeak mix measured **−21.4 LUFS**. With the nested setting, the full export measured **−14.1 LUFS**. A one-second direct-parameter export measured −14.2. The script uses the nested setting.

**Ease failed once.** `effects.setInterpolation` with `easeOut` on the second clip returned "no keyframe at that time". The linear scale keyframes were still there, and the yellow square grew. I did not get a confirmed ease curve.

**PyAV 19 vs faster-whisper 1.2.1.** `av.open(..., metadata_errors="ignore")` raises `TypeError` on the av that pip installed (19.0.2). `scripts/transcribe.py` drops that keyword. Decoding then works.

**Caption model.** `base` int8 on this same clip heard the first line as "Just rest it, you're cut before you know this." `small` int8 heard the script, plus "Sint," at the start of the lines after a pause. `small` is the default. It cost 1.0 s to load from cache and 1.7 s to transcribe 15 s of audio, peak RSS 771 MB. `base` was 0.6 s load + 0.6 s transcribe and 365 MB, and the captions would have been wrong. "Sint" is still burned into the `small` export. A person has to read the transcript before this is publishable. Real speech was not tested. espeak is a harsh ASR input, so this is a lower bound on caption *risk*, not a measurement of clinic audio.

## HEVC, .MOV, and 9:16

9:16 export works. The sequence was created at 1080×1920, and the built-in preset `Social Vertical 1080×1920` writes that size. ffprobe reports DAR 9:16, H.264 High, yuv420p.

HEVC in a QuickTime `.MOV` with the `hvc1` tag **does** import, for files ffmpeg made:

- 8-bit 720×1280 HEVC + AAC, extension `.MOV`: probe says HEVC, render writes a real test-pattern PNG (not an offline placeholder).
- 10-bit 640×360 HEVC (`yuv420p10le`): probe says "YUV 4:2:0 10-bit", and a rendered frame is not black.

That is not an iPhone file. It does not cover a 977 MB camera original, 4K, Dolby audio, log/HDR, or a rotation matrix. I could not get ffmpeg 6.1.1 to write a QuickTime display matrix with `-metadata:s:v rotate=90` (ffprobe showed no side data), and FilmCraft's probe JSON has no rotation field. Whether a portrait iPhone `.MOV` that is stored as 1920×1080 plus a 90° matrix comes in upright is **unverified**. If the proxy arrives sideways, bake the rotation with ffmpeg before import and say so. Do not assume the alpha decoder matches every iPhone file until one has been through `probe` and a rendered frame.

## Time and RAM, and what that implies for a weekly video

Measured on this 4-core VM, 1080×1920, CPU only:

| Step | Wall | Peak RSS |
| --- | --- | --- |
| Synthetic clip (ffmpeg + espeak) | 3.5 s | 366 MB |
| Whisper `small`, model already cached | 3.0 s (1.0 s load + 1.7 s transcribe) for 15 s of audio | 771 MB |
| Whisper `base` (wrong transcript) | 1.3 s | 365 MB |
| FilmCraft edit + export, 272 frames | 16.6 s at 16.6 fps | 1.31 GB |
| HEVC probe + two frame renders | 0.5 s | 232 MB |

A 45-second finished video at the same 16.6 fps is about 80 seconds of encode, if the rate holds. I did not export a 45- or 60-second timeline, and I did not decode a 4K HEVC original, so treat that as a scaling of this one measurement. Transcription of a one-minute human take was not timed either. The agent deciding the cut is extra and was not the slow part here: the rules are a phrase match and a 0.45 s gap collapse.

Disk for one synthetic run is small (the export is 14 MB). A 977 MB source plus a FilmCraft project and an export is a different disk bill, and it was not exercised.

## Quality against a human edit

**Not compared.** The human file `1 - 2026-10-23 - Why Stress Hits Your Gut.mp4` was not here. I will not invent its caption size, zoom cadence, or music.

What this synthetic pass already shows a reviewer would reject:

- A made-up word, "Sint,", on screen.
- Captions are one word at a time in Inter, low on the frame. A clinic caption that highlights the current word inside a phrase is a different object, and this pipeline does not build it.
- The zoom is one linear ramp on scale. No ease (the ease call failed), no punch on a hard word, no reset.
- No music, no room tone under the cuts, no intro or end card.
- Cuts are "drop this sentence and gaps longer than 0.45 s". They are not an editor choosing a breath.

## Recommendation

Ship the loop as a **rough cut generator** once the real proxy has been used to lock a style spec. Keep a person on the transcript and on the final watch-through. Publishing the agent's MP4 untouched will put ASR errors and a generic zoom on the clinic's account.

For a weekly production path I would want, in order:

1. The two proxies, and a written style spec filled from them (`config/STYLE_SPEC.md`).
2. A transcript review step that blocks export. `small` was good enough to find the cut line and not good enough to burn unattended.
3. Confirmation on one real iPhone `.MOV`: upright, full frame, audio in sync, no offline media. Transcode only if that fails.
4. The caption treatment the human file actually uses. If it is a highlighted phrase, word-level SRT is the wrong tool and needs a different title/graphic approach.
5. Music and mix, if the human cut has them. Loudness to −14 is available. A bed is not.
6. A length check on a real minute-long timeline (RAM and encode time), ideally with a GPU later. CPU export works. It is the slow step.
7. FilmCraft is alpha (0.12.0, their own codecs). Pin the version. Re-run `scripts/run_e2e.sh` on upgrade. The razor/duration bug is the sort of thing that will bite a timeline built the way an editor thinks.

## What I could not verify

- Any pixel of the clinic raw or the human final.
- iPhone HEVC (rotation, 4K, camera audio, a 977 MB file).
- Whisper on a real voice.
- True-peak compliance beyond passing the −1.5 dBTP setting. I measured integrated loudness only.
- An eased zoom curve.
- The desktop app, anywhere it has a working GPU surface.
- Encode time and RAM for a 30–60 s timeline or a 4K source.
- Whether `effects.setInterpolation` can be made to see the keyframe with a different time base. I left the linear ramp in place.

## What I need for the next pass

Low-resolution proxies of `IMG_7929.MOV` and `1 - 2026-10-23 - Why Stress Hits Your Gut.mp4`, each under 15 MB. Same picture as the originals, including burned-in captions on the final. Drop them in `filmcraft-feasibility/incoming/` or attach them to the follow-up. Chunks are fine. Do not send anything that identifies a patient. I will not upload them.
