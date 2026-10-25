# Results

**An agent can drive the mechanical edit. On this video it cannot replace the editor, and it cannot rebuild the human cut from the raw that was supplied.**

FilmCraft 0.12.0's command-line tool, with no window and no GPU, did the mouse work on a 15-second synthetic 9:16 clip: drop a sentence, ramp a zoom, burn captions, hit about −14 LUFS, write 1080×1920 H.264. That part works. The details are below.

The Week 48 proxies do not extend that into a clinic edit. The raw proxy (a low-resolution copy of `IMG_7929.MOV`) and the human final ("Why Stress Hits Your Gut") are **different recordings**. Whisper `small` token overlap is **0.052**. The only shared phrase of four words or more is "your gut and your gut". A FilmCraft rough cut was not exported. Placing this raw on a timeline cannot produce that final, and inventing a stress script to fill the gap would be a fake comparison.

The transcript below is Whisper `small`, cross-checked against Whisper `medium` and against the final's burned-in captions where tesseract could read them. Low-confidence words are flagged. Jackson will edit the wording later. Nothing in either proxy identified a patient.

## Week 48 proxies

Both files were probed with ffprobe and with `filmcraft-cli probe` (0.12.0, headless). FilmCraft opens them as MPEG-4, H.264 High, 8-bit 4:2:0, BT.709, AAC mono 48 kHz. The probe JSON has no rotation field. These copies are already upright.

| | Raw proxy | Human final |
| --- | --- | --- |
| What it is | Low-res copy of `IMG_7929.MOV`. Rotation already applied. SDR, not tonemapped. The camera original is 4K HEVC 60 fps HLG. This file is not that original. | Low-res copy of the captioned master. Master is 1080×1920 at 60 fps. |
| Picture | H.264 High, 202×360, 30 fps, yuv420p | H.264 High, 360×640, 30 fps, yuv420p, DAR 9:16 |
| Audio | AAC LC, 48 kHz, mono, ~65 kb/s | AAC LC, 48 kHz, mono, ~65 kb/s |
| Duration | 162.367 s | 69.933 s (2098 frames) |
| Size | 11.2 MB | 8.4 MB |
| Speech | Antibiotics do not kill a cold. Each line is said twice. | Stress, the gut, the vagus nerve, a breathing cue, sleep / fibre / magnesium |
| Whisper `small` tokens in common | ratio 0.052 (395 raw tokens, 262 final tokens) | same |
| Picture | Histogram correlation 0.368 against the final frame at 2 s | Talking head for most of the 70 s |
| Loudness | −27.1 LUFS, range 11.3 LU, true peak −4.5 dBFS | −13.4 LUFS, range 2.0 LU, true peak +0.7 dBFS on this proxy |
| Silence | 51 gaps ≥ 0.35 s below −35 dB, 39.35 s total | No gap ≥ 0.20 s below −35 dB. 0.4% of 100 ms windows are below −35 dBFS |
| Captions | None seen | White phrase captions in the middle of the frame, plus a 2-line hook |

The +0.7 dBFS peak is on a ~65 kb/s AAC proxy of a 60 fps master. It may be the proxy encode. Do not treat it as the master's true peak.

These proxies do not test iPhone HEVC, a rotation matrix, 4K, or HLG. The synthetic HEVC probe further down is still the only HEVC evidence, and those files were made by ffmpeg.

### Transcript of the final

Primary model: faster-whisper **`small`**, int8, CPU, beam 5, word timestamps, `vad_filter` off. 7.4 s wall, mean word probability **0.955**.

`medium` on the whole file (25.6 s, 179 words, mean 0.895) **dropped two stretches that are captioned on screen**: 21.4–30.6 s (vagus nerve and the hormones) and 45.2–61.4 s (head and gut, then the breathing cue). Run again on those spans alone, medium heard them and agreed with `small`. `small` is the transcript. `medium` is the cross-check. Where they disagree, both wordings are below.

```
0.00  in your stomach before you go into a big meeting,
3.04  it's not actually in your head, it's actually in your gut.
5.06  Stress, tummy is one of the most common things
7.32  that patients complain of to me.
8.82  What you may not know is that your gut
10.14 has its own nervous system.
11.54 It has hundreds of millions of neurons
13.78 devoted to its own sensations.
15.72 Now this is more than you have in your spinal cord
17.38 and this is why we refer to the gut nervous system
20.32 as the second brain.
21.44 Now your gut nervous system is wired directly
23.40 into your brain via the biggest cranial nerve,
25.80 the vagus nerve.
26.64 So when you're stressed, your body releases hormones
28.60 like cortisol, adrenaline, nor adrenaline.
30.94 The effect of these hormones is it can slow
33.00 your stomach down, but your bowel can speed up
35.84 and your gut becomes far more sensitive.
38.44 That's the knot in your stomach
39.62 that's sudden churning in your gut
41.44 and then the need to rush to the toilet.
43.42 So is it all in your head?
44.54 Well, not quite, it's a two-way street.
46.32 Your head affects your gut
47.66 and your gut affects your head,
49.14 which means you can work on this from both ends.
51.44 In that moment of stress, slow your breathing down,
54.02 breathe in for four, breathe out for six
56.12 for one to two minutes.
57.22 A long outbreath quickly tells your nervous system
60.48 that it is safe.
61.56 Longer term, protect your sleep, eat more fiber
63.98 and look at taking some magnesium supplement.
66.24 Those three things will help your gut handle stress
69.06 every day.
```

Readable center-band OCR (tesseract, 3× lanczos, once a second). These lines match `small`. The other seconds were illegible at 360 px wide; that is the OCR failing, not the transcript drifting.

| t | OCR | Whisper nearby |
| --- | --- | --- |
| 0–2 s | Your Stomach Knots / Before Big Events? | Not the spoken line. It is a title. |
| 3 s | it's not | it's not actually in your head |
| 7 s | is one of the most common things | matches |
| 8 s | that patients complain | matches |
| 35 s | but your bowel | matches |
| 39–41 s | that's / that sudden | that's the knot / that sudden churning |
| 47 s | your head affects | matches |
| 48–49 s | and your gut / and your gut affects your head | matches |
| 50–51 s | you can work / from both ends | matches |
| 53 s | slow your | slow your breathing |
| 57 s | for | breathe in for four |
| 65–66 s | magnesi… | magnesium |
| 69 s | handle stress | matches |

The hook occupies the caption band from about 0 to 2.5 s and is gone by 6 s.

### Words to fix on the final

Jackson edits these. Probabilities are Whisper's, not a fact.

| Time | `small` | p | Other hearing | Why it is flagged |
| --- | --- | --- | --- | --- |
| 0.0 s | "in" | 0.03 | Isolated `medium`: "Now that knot in your stomach before you go into a big meeting…" (mean 0.95; "knot" 0.59) | `small` started mid-phrase. The hook card is the paraphrase of the medium line. Prefer the medium opening. |
| 5.5 s | "tummy" | ≥ 0.70 | `medium` "tummy" 0.54 | Both models heard it. May be the phrase "stress tummy". OCR did not catch this word. |
| 14.6 s | "its" | high | Full-file `medium` "it's" 0.52 | Prefer "its". |
| 15.8 s | "this" | 0.61 | heard by both | Filler. |
| 17.4 s | "and" | 0.48 | `medium` 0.44 | Filler. |
| 28.6 s | "like" | 0.41 | clip confirms "hormones, like cortisol, adrenaline, noradrenaline" | The hormone names themselves are solid (`cortisol` 0.97, `adrenaline` 0.91). "like" is the weak word. |
| 30.9 s | "slow your stomach down" | stomach not under 0.70 | Full-file `medium`: "slow you down" ("you" 0.67, and the segment opens at 0.11) | OCR at 33 s did not read it. Unresolved. |
| 35.8 s | "and" | 0.53 | | Filler, before "your gut becomes far more sensitive". |
| 45.8 s | "street" | 0.62 | Isolated `medium`: "streak" 0.47 | OCR did not read either word. "Street" is the higher probability and the ordinary idiom. Unresolved. |
| 56.1 s | "for" | 0.29 | Isolated `medium` "for" 0.52, and the clip has the whole cue "breathe in for four, breathe out for six" | OCR at 57 s reads "for". The cue is real. The single word probability is low. |
| 63.6 s | "fiber" | 0.56 | `medium` "fibre" 0.73 | Spelling unresolved. OCR did not read it. |
| 65.5 s | "supplement" | 0.66 | `medium` 0.53 | "magnesium" is 1.00 on `small`, and OCR saw "magnesi". "Supplement" is the weak word. |

### Transcript of the raw

`small`: 13.3 s wall, mean word probability **0.923**. The recording is paired takes. A gap of about a second, then the line again. A splitter that only breaks on gaps longer than 1 second glues each pair into one long take. The pairs are the structure.

`medium` on the raw took 78.4 s, 423 words, mean probability **0.842**. It agreed on the spine and on the surname, and it also invented words (below). It is not the transcript.

| Start | First take (`small`) | Second take (`small`) |
| --- | --- | --- |
| 4.1 / 7.1 | Antibiotics can't kill a cold. You know that, right? | So antibiotics can't kill a cold. You know that, right? |
| 10.9 / 16.3 | I'm Dr Paul Froome's gastroenterologist, and I've seen over 10,000 microbiomes in 25 years. | I'm Dr Paul Froome's gastroenterologist, and I've seen over 10,000 microbiomes over 25 years. |
| 21.5 / 25.8 | And every winter I still meet people who took antibiotics for a cold just in case. | And every year I see loads of people that take antibiotics for a cold just in case. |
| 32.0 / 36.9 | So a cold is a virus. Antibiotics only kill bacteria. | So you remember, a cold is just a virus. Now antibiotics only kill bacteria. |
| 43.4 / 48.8 | So when you take them for a cold, the only bacteria they hit are the ones living in your gut. | So when you take antibiotics for a cold, the only bacteria they hit are the ones living in your gut. |
| 54.2 / 57.4 | And your gut doesn't bounce back by the weekend. | And your gut doesn't just bounce back by the weekend. |
| 60.2 / 64.6 | A team in Copenhagen gave 12 healthy men a 4 day course of antibiotics. | So a team in Copenhagen gave 12 healthy men a course of antibiotics. |
| 69.8 / 72.4 | Then tracked their gut bacteria for 6 months. | Then tracked their gut bacteria for over 6 months. |
| 75.9 / 81.6 | Now most species came back within about 6 weeks, but some common ones were still missing at 6 months. | Now while most bacterial species returned within 6 weeks, some critical common probiotic species remained depleted. |
| 95.7 / 99.5 | Remained gone at 6 months. | Some common important probiotic species were still gone at 6 months. |
| 107.8 / 110.8 | Now this route shows you how long the damage can last. | Now this study shows you just how long the damage from antibiotics can sometimes last. |
| 119.0 / 122.3 | So should you downright refuse antibiotics? | So should you downright refuse antibiotics? |
| 124.6 / 126.9 | No, I mean they've saved many lives. | No, if you have a bacterial infection, very important and of course they've saved many many lives. |
| 132.4 / 134.7 | Just don't ask for them when you have a cold. | Just don't ask for antibiotics when you have a viral cold. |
| 138.6 / 142.2 | Rest, drink fluids and give it 7 to 10 days. | Rest, drink plenty of fluids, give it 5 to 7 days. |
| 146.7 / 150.7 | And if you're getting worse after that or you have a high fever or trouble breathing? | Now if you're getting worse after that or if you have a high fever, or you're having trouble breathing, |
| 156.7 / 158.6 | You definitely go back to your GP. | That's different. Probably bacterial, go back to your GP. |

Content words to fix on the raw:

| Word | `small` | `medium` | Note |
| --- | --- | --- | --- |
| Paul | 0.66 at 11.3 s, **0.03** at 16.6 s | 0.99 on both takes | The name is stable. The first-pass probability is not. |
| Froome's | 0.60 at 11.6 s, 0.99 at 17.1 s | 0.78 and 0.97 | Both models wrote **Froome's**, with an apostrophe. The brief spells the doctor **Froomes**. Spelling is unconfirmed. |
| 10,000 | first "10" is 0.48; second take 1.00 | second take agrees | Prefer the second take. |
| in / over 25 years | both takes, high | agrees | The takes themselves differ ("in" vs "over"). |
| every winter / meet people | `small` is the readable line | `medium` heard "make money" and "see others" with probabilities at or near 0 | Reject the medium line. |
| 4 day / four-day | "4" is 0.57, first take only | Same words, but medium's word probabilities on the whole Copenhagen sentence collapsed to 0 | The second take, in both models, drops "4 day". Keep the sentence, flag "4 day". |
| route / study | "route" 0.72, then "study" 0.97 | "route" 0.58, then "study" 0.98 | The repeat says "study". "Route" is the weak first take. |
| downright | 0.82 and 0.95, both takes | 0.93 and 0.98, both takes | Both models, both takes. Odd word. Check whether it was "outright". Not corrected here. |
| 7 to 10 days / 5 to 7 days | the takes disagree; "7" is 0.60 | "seven" 0.47, then "five to seven" | A real difference between takes, not a one-model slip. |
| 6 (weeks) | 0.16 at 85.0 s on the second take | the phrase is present | The other "6" tokens are above 0.7. |

`medium` also inserted "depletedtalk forgot by how long" between the probiotic line and "at six months", with several probabilities at 0. That span is not in the `small` transcript. Drop it.

Function words under 0.50 on the `small` raw pass, listed so they are not silent: So 0.48 (7.1 s), over 0.35 (20.2 s), who 0.45 (23.2 s), a 0.42 (32.3 s), So 0.30 (48.8 s), And 0.46 (54.2 s), And 0.03 (57.4 s), A 0.30 (60.2 s), So 0.003 (64.6 s), antibiotics 0.32 (68.5 s, end of the second Copenhagen line), Then 0.10 (72.4 s), Now 0.40 (81.6 s), while 0.42 (82.0 s), Now 0.49 (110.8 s), So 0.17 (122.3 s), and 0.31 (129.8 s), You 0.14 (156.7 s).

### What the human edit looks like

Full measurements: [`config/week48.style.yaml`](config/week48.style.yaml).

- **Captions.** White, no box, vertical middle (glyph body about 49–52% of the way down the 640 px proxy, roughly 17–20 px tall, one line). Phrases of about 2–6 words, changing about once a second, tracking the voice. Not karaoke, and not a full sentence. Fill on a clean frame is median RGB [255, 255, 251], with a dark neighbor (outline or shadow). Stroke width and font name are not recoverable at 360 px. If this proxy is exactly one third of a 1080×1920 master, that glyph height is about 50–60 px. That is a scale guess.
- **Hook.** About 0–2.5 s, two lines in the same band: "Your Stomach Knots" / "Before Big Events?".
- **Cuts.** ffmpeg scene score > 0.35 at 8.8, 30.9, 34.07, 43.4, 46.23, 51.43 s. The cuts at 8.8 and 43.4 stay on a normal talking-head photograph. From 30.9 to 34.1 the frames at 30 s and 32 s are dark (mean luma about 21 and 26) and tesseract read nothing; 34 s is the talking head again. From 46.2 to 51.4 the frame is a flat near-black field, median RGB about [6, 12, 18], still carrying the white speech caption, plus brighter shapes above the line and (at 48–50 s) below it. Those shapes did not OCR. They are not named. There is no readable lower-third name bar.
- **Zoom.** Not established. A 4-second scale search (1.00–1.30) prefers 1.00 in most windows. The window at 60 s prefers 1.15 (correlation 0.74 vs 0.59). Windows at 20 s and 24 s go negative, which is a cut, not a zoom.
- **Loudness.** −13.4 LUFS, range 2.0 LU, almost no quiet. A music bed under that limited voice would not show up in this meter. None is claimed. The synthetic pipeline's one-word lower-fifth caption is a different object than this final.

### Rough cut

Not made. `scripts/analyze_week48.py` sets `rough_cut.feasible` false when the token ratio is under 0.35. The ratio is 0.052. The final's words are not in this raw, so there is no source range to place, no caption timing to copy onto this picture, and no honest side-by-side of an export. FilmCraft did **open** both proxies (`probe` exit 0). That only shows the H.264 copies decode.

## What the synthetic pass produced

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

Those synthetic captions are one word at a time, low in the frame, in Inter. The clinic final is a short phrase in the middle, with a two-line hook. `config/edit.json` is not the style spec.

I looked at extracted frames. Early in the clip the grid is small and the yellow square is 200 px. Near the end the grid lines are thicker and the square is larger, which is the punch-in. The caption sits in a translucent dark bar low in the frame, one word at a time. FilmCraft's caption track has one style for the whole cue, so word-by-word here means a new cue per word.

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

- ffmpeg **6.1.1** was already on the image (`ffmpeg version 6.1.1-3ubuntu5`). Used for the synthetic clip, ffprobe, ebur128, silencedetect, and the scene detector. FilmCraft does not shell out to ffmpeg to decode or encode.
- espeak-ng **1.51** from apt.
- tesseract **5.3.4** from apt, used only on the final proxy's caption band.
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
| `probe` | Week 48 proxies. Both returned H.264 High, AAC, 30 fps. Raw 202×360, final 360×640. |

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

**PyAV 19 vs faster-whisper 1.2.1.** `av.open(..., metadata_errors="ignore")` raises `TypeError` on the av that pip installed (19.0.2). `scripts/transcribe.py` and `scripts/transcribe_week48.py` drop that keyword. Decoding then works.

**Caption model on the synthetic voice.** `base` int8 on this same clip heard the first line as "Just rest it, you're cut before you know this." `small` int8 heard the script, plus "Sint," at the start of the lines after a pause. `small` is the default. It cost 1.0 s to load from cache and 1.7 s to transcribe 15 s of audio, peak RSS 771 MB. `base` was 0.6 s load + 0.6 s transcribe and 365 MB, and the captions would have been wrong. "Sint" is still burned into the `small` export. espeak is a harsh ASR input, so this is a lower bound on caption risk. The clinic proxies are a separate measurement, above.

**`medium` is not automatically better.** On the clinic final it skipped captioned speech until those spans were cut out and transcribed alone. On the clinic raw its mean probability was lower than `small` and it added a sentence that is not in the `small` transcript. Use `small` for the full file. Use a second model, and the burned-in words, to challenge it.

## HEVC, .MOV, and 9:16

9:16 export works. The sequence was created at 1080×1920, and the built-in preset `Social Vertical 1080×1920` writes that size. ffprobe reports DAR 9:16, H.264 High, yuv420p.

HEVC in a QuickTime `.MOV` with the `hvc1` tag **does** import, for files ffmpeg made:

- 8-bit 720×1280 HEVC + AAC, extension `.MOV`: probe says HEVC, render writes a real test-pattern PNG (not an offline placeholder).
- 10-bit 640×360 HEVC (`yuv420p10le`): probe says "YUV 4:2:0 10-bit", and a rendered frame is not black.

That is not an iPhone file. It does not cover a 977 MB camera original, 4K, Dolby audio, log/HDR, or a rotation matrix. I could not get ffmpeg 6.1.1 to write a QuickTime display matrix with `-metadata:s:v rotate=90` (ffprobe showed no side data), and FilmCraft's probe JSON has no rotation field. Whether a portrait iPhone `.MOV` that is stored as 1920×1080 plus a 90° matrix comes in upright is **unverified**. The Week 48 proxies do not answer it: rotation was baked in before they reached this machine, and they are H.264.

## Time and RAM

Measured on this 4-core VM, CPU only:

| Step | Wall | Peak RSS |
| --- | --- | --- |
| Synthetic clip (ffmpeg + espeak) | 3.5 s | 366 MB |
| Whisper `small`, model already cached, 15 s espeak | 3.0 s (1.0 s load + 1.7 s transcribe) | 771 MB |
| Whisper `base` (wrong synthetic transcript) | 1.3 s | 365 MB |
| FilmCraft edit + export, 272 frames at 1080×1920 | 16.6 s at 16.6 fps | 1.31 GB |
| HEVC probe + two frame renders | 0.5 s | 232 MB |
| Whisper `small`, Week 48 raw 162 s | 13.3 s | not recorded separately |
| Whisper `small`, Week 48 final 70 s | 7.4 s | not recorded separately |
| Whisper `medium`, Week 48 final, first load from the hub | 12.4 s load + 25.6 s transcribe | not recorded |
| Whisper `medium`, Week 48 raw, model cached | 3.1 s load + 78.4 s transcribe | not recorded |

`small` on the real voice was faster than realtime by a wide margin on this CPU. `medium` on the 162 s raw was about 2× realtime and the less accurate of the two. A 45-second FilmCraft export at the synthetic 16.6 fps would be about 80 seconds of encode, if the rate holds. I did not export a 45- or 60-second timeline, and I did not decode the 4K HEVC original.

## Recommendation

Keep the synthetic loop as proof that the headless CLI can cut, zoom, burn captions, and export 9:16. Do not point it at Week 48 Video 1 and expect the human final.

What would have to be true before an agent rough-cut is even a fair test:

1. The raw and the final have to be the same take. These two are not. Token ratio was 0.05. The threshold in `scripts/analyze_week48.py` is 0.35, and it correctly refused.
2. A person edits the transcript before anything is burned. `small` matched the captions it could be checked against, and it still left "street"/"streak", "fiber"/"fibre", "stomach"/"you", and the surname spelling open. The synthetic export already burned the invented word "Sint".
3. The caption tool has to place a short phrase in the middle of the frame, plus a two-line hook that is not the spoken sentence. One-word SRT in the lower fifth is the wrong treatment for this final.
4. One real iPhone `.MOV` still has to be probed: upright, full frame, audio in sync. These H.264 proxies do not count.
5. Music, if the master has it, is a separate stem. Loudness to about −14 LUFS is available. A bed was not audible as its own object under this limited mix.
6. FilmCraft is alpha (0.12.0). Pin the version. The razor/duration bug is the sort of thing that will bite a timeline built the way an editor thinks.

## What I could not verify

- The 4K HEVC camera original, including rotation, HDR, and a 977 MB decode.
- Font name, exact outline width, and master-resolution caption size. The 50–60 px figure is a ×3 scale of a 360 px proxy.
- Whether the dark stretch at 31–34 s and the shapes on the near-black card at 46–51 s are B-roll, a sticker, or a grade. The pixels say "not the talking head." They do not say what the graphic is.
- A punch-in cadence. One window preferred 1.15×.
- A music bed.
- True peak of the master.
- An eased zoom curve, on the synthetic test.
- The desktop app, anywhere it has a working GPU surface.
- Encode time and RAM for a 30–60 s timeline or a 4K source.
- Whisper's surname spelling. Both models wrote "Froome's".
