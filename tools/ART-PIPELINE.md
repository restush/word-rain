# Word Rain Art Pipeline

Developer documentation for how the classroom art was generated, cleaned, converted,
and placed. Everything here is from the actual production run (2026-11). Every command
below was really used; no invented flags.

## 1. gcloud setup (one-time)

The Google Cloud SDK originally lived in `~/Downloads/google-cloud-sdk` and later vanished
(DL cleanup). Reinstall:

```bash
brew install --cask google-cloud-cli
```

Auth rides on Application Default Credentials, project `finishyourgame`:

```bash
gcloud auth application-default print-access-token
```

Known trap: installers patch `~/.zshrc` (interactive shells only). Login and agent shells
source `~/.zprofile`. If `gcloud` is "command not found" in scripts but works in your
terminal, source the SDK `path.zsh.inc` from `~/.zprofile`, never per-command PATH exports.

## 2. Image generation: Nano Banana 2.1

Model `gemini-nano-banana-2.1` via Agent Platform REST:

```bash
POST https://aiplatform.googleapis.com/v1/projects/finishyourgame/locations/global/publishers/google/models/gemini-nano-banana-2.1:generateContent
Authorization: Bearer <token from gcloud auth application-default print-access-token>
```

Request body shape that worked:

```json
{
  "contents": [{"role": "user", "parts": [
    {"text": "<prompt>"},
    {"inline_data": {"mime_type": "image/png", "data": "<base64 of reference image>"}}
  ]}],
  "generation_config": {
    "response_modalities": ["TEXT", "IMAGE"],
    "image_config": {"aspect_ratio": "1:1", "image_size": "1K"},
    "thinking_config": {"thinking_level": "MEDIUM", "include_thoughts": false}
  }
}
```

Response image: `candidates[0].content.parts[].inlineData.data` (base64 PNG). The base
scene is passed as `inline_data` reference so geometry and style match the classroom.

Rate limits are real: sleep 20s between generations, and retry HTTP 429 with backoff
30s, 60s, 90s. The generator script does the backoff automatically.

Prompting recipes (all end with the shared STYLE sentence):

STYLE: "16-bit pixel art, 45-degree isometric room-box style, thick clean outlines,
limited warm palette: cream walls, teal accents, warm wood browns, soft ambient shadows,
dithered shading, no text, no letters, no numbers, no people, no watermark."

- Add-on sprite (new object on wall or floor): "Using the attached classroom image ONLY
  as reference for size, isometric angle and pixel-art style. Draw ONLY <object>,
  isolated on a plain pure white background. No wall, no floor, no room, nothing else." + STYLE
- Replacement sprite (covers an old object): same recipe plus "exactly the same size and
  footprint as <old object> in the reference", example: the whiteboard must fully cover
  the blackboard or the old frame peeks out.

Hard rules learned the expensive way:
- Say "no wall mount, no VESA bracket, no arm, no stand" explicitly or the model adds
  fixtures (the TV VESA incident).
- State proportions in words: "tall and narrow, about twice as tall as wide, 2 panes wide
  and 3 panes tall" (the square-window incident).
- Kaligrafi and anything Arabic-looking: "strictly NO letters, NO writing, NO script of
  any kind, pure geometry only". Red line: never AI-generated Arabic script.

## 3. Background removal: withoutBG open model (Local API)

```bash
curl -sS -X POST 'http://127.0.0.1:8000/v1/remove-background?output=cutout' \
  -F "image=@input.png" -o output-cut.png
```

Local Mac app (withoutBG open weights), verify with `GET /health`. It never calls the
cloud. If you use the proper-pixel-art route below, its `--transparent` output replaces
this step entirely.

## 4. Noisy pixel art to true pixel art: proper-pixel-art

AI pixel art is painted at high resolution with noisy edges and a non-uniform grid, so
plain downsampling blurs it. `proper-pixel-art` (Python) recovers the true pixel grid
(Canny edges, Hough lines, mesh estimation) and re-renders one flat color per pixel:

```bash
uvx --from "proper-pixel-art" ppa input.png -o out.png -t -u 4 -w 6
```

- `-t`: transparent output (also replaces the withoutBG step)
- `-u 4`: initial upscale, catches pixel edges the detector would otherwise miss
- `-w 6`: pins the pixel width so every sprite shares one chunk size

Lessons from the test runs:
- Convert from the RAW PNG generation, not the lossy WebP export.
- Clean stray generated objects BEFORE converting. The double-fan sprite came back in a
  converted asset because the raw still contained the second fan.
- Pin `-w` across the whole set. Per-image auto detection produced inconsistent chunk
  sizes (135px, 216px, 271px canvases in the 3-image test).
- Palette mode (`-c`) crushed the warm browns on test art, so keep the default dominant
  color method.
- `-s` (scale-result) is for previews only. Ship the 1x grid and let CSS scale it:
  `image-rendering: pixelated`.

## 5. End-to-end flow

1. Generate raw PNG with Nano Banana 2.1 (section 2), one prompt per recipe.
2. Clean the raw: remove stray generated objects first (fans, mounts, duplicates).
3. Convert: `ppa input.png -o out.png -t -u 4 -w 6` (or the withoutBG cutout on the old path).
4. Save as `*-cut.webp` into `project/word-rain/assets/`.
5. Placement: coordinates live in the `SCENE` and `SHOP` tables in `index.html`, hand-tuned
   with `project/word-rain/tools/layer-tuner.html` (drag, resize, rotate, skew, flip) and
   stored in `project/word-rain/tools/slots.json`.

Generator script with every prompt and the 429 backoff: `project/word-rain/tools/gen_classroom.py`.


## ERRATA (after the first full-set batch, 2026-11-14)
- The fixed `-w 6` recipe is WRONG for scene-wide use: it produces fine grids that mush at phone scale. Correct recipe: per-sprite pixel width `pw = round(content_raw_width * CHUNK / slot_display_width)` with CHUNK = 6 stage-px (about 2.3 device px on phones). This yields pw 6 for big surfaces and pw 20-50 for small items, giving uniform chunk size across the scene.
- ppa outputs are NOT content-cropped: crop each output to its alpha bbox before saving as the -cut.webp (shell-base is the exception: keep full canvas, the game displays it at 1024).
- Convert from raw PNG only; save results as lossless WebP (about 1KB per small sprite, whole set about 20KB).
- CSS `image-rendering: pixelated` is NOT sufficient on phones (2026-11-15). Per spec it is nearest-neighbour only up to the nearest integer multiple, then smooth interpolation to the final size; WebKit additionally rasterizes transformed layers (our rotate/skew/scale sprites) through the compositor's linear filter. The art itself was fine — the fix is rendering: draw the scene into one `<canvas>` with `ctx.imageSmoothingEnabled = false` (a spec-guaranteed point-sample on every engine, the same backbuffer trick game engines use), backing store sized to whole device pixels.
