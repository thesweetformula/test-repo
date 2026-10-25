# Style spec

Week 48 Video 1 is measured in [`week48.style.yaml`](week48.style.yaml). That file is the spec. This page is the short version.

The two proxies are **not the same recording**. The raw is a double-taken antibiotics script (`IMG_7929.MOV`, 162 seconds). The human final is "Why Stress Hits Your Gut" (70 seconds). Whisper token overlap is 0.05. A FilmCraft rough cut of this raw was not made, because the final's words are not in the raw.

What the human final actually does, measured on the 360×640 proxy:

- Captions sit in the **vertical middle**, white, no background box, about 2–6 words at a time, held for about a second. Not one word at a time, and not a full sentence.
- The first 2–3 seconds are a two-line hook, "Your Stomach Knots" / "Before Big Events?", in that same band. It is not the spoken line.
- Loudness on this proxy is about **−13.4 LUFS**, loudness range 2 LU. Almost no silence. A music bed was not separable from the voice.
- Six hard cuts. Two of them stay on the talking head. One stretch (about 31–34 s) is a dark picture that did not OCR. One stretch (about 46–51 s) is a near-black card that still carries the speech caption, plus shapes tesseract could not read. Those shapes are not named.
- A steady punch-in was not measurable. One 4-second window near 60 seconds preferred a 1.15× scale. The rest did not.

`config/edit.json` is only the synthetic test. It burns one word at a time in the lower fifth. That is a different caption than this final.

The transcript Jackson will edit, and the words Whisper was unsure of, are in [RESULTS.md](../RESULTS.md).
