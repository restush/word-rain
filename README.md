# Word Rain (Hujan Kata)

Lightweight portrait browser game for English vocabulary, with a classroom renovation game on top. Words rain down: tap the right ones. Score earns coins, coins fix up a pixel classroom.

**Play: https://restush.github.io/word-rain/**

Made for SDIT Baitussalam 2 Cangkringan (Fase B, English).

## How to play
- Pick a pack (Animals / Colors / Food / School / Mixed), press **Start Word Rain**.
- Tap the correct falling words. Correct = +10, wrong = -5.
- The energy bar drains over time and refills on correct taps. Empty bar = run over.
- 3 lives. Mutation cards (skull) cost a life when tapped, and might when they fall.
  Heart cards refill a life (only appear when lives < 3).
- Round types rotate: picture prompt, category rush, listen and tap, picture match.
- Score becomes coins: floor(score / 20) + 5 per level.

## Classroom (renovation meta)
Spend coins on 15 shop items: repairs (Fix Window, Whiteboard, Air Conditioner,
New Tiles, Wall Paint), equipment (Smart TV), wall decor (World Map, Picture Poster,
Geometric Art, Flag, Display Board, Curtains), cozy items (Bookshelf, Prayer Rug,
Potted Plants).

Layer rules:
- `replaces`: an upgrade hides the old item at the same spot.
- `clears`: buying an item hides old leftovers its footprint covers.
- `requires`: Geometric Art needs the AC first, Curtains needs the fixed window
  (the item is hidden in the shop until then).

Coins and purchases persist in the browser (localStorage).

## Offline (PWA)
First visit needs internet (the QR scan). After that the game runs fully offline.
"Install untuk offline" adds a home-screen icon (Android).

## Editing content (teachers)
Open `index.html`, edit the tables at the top of the script only:
- `CONTENT`: word lists (en / id / pic / tag)
- `CONFIG`: difficulty, coins, prices. `debugPrice: 1` makes everything cost 1 coin
  (debug), set to `0` for real prices.
- `ROUND_PLAN`: prompt type rotation.

## Art pipeline (new sprites)
- `tools/gen_classroom.py`: Nano Banana 2.1 generation via Agent Platform REST
  (needs gcloud auth). `python3 tools/gen_classroom.py <name> [prompt] [ref.png]`
  Prompts for all 28 layers are built in.
- Cutouts: withoutBG Local API (`http://127.0.0.1:8000/v1/remove-background?output=cutout`),
  then crop each cutout tight to its content.
- `tools/layer-tuner.html`: interactive placement (drag, resize, rotate, skew, flip,
  before/after groups) that emits slot JSON. Paste JSON + Apply round-trips.
- `tools/composite.py`: batch compositing and alignment tests.
- `tools/slots.json`: hand-tuned layer layout, the scene source of truth.
- `tools/conflicts.json`: footprint-overlap map used to design the layer rules.

## Structure
- `index.html`: the whole game (single file, vanilla JS, zero dependencies)
- `assets/`: scene layers (shell-base + 27 cutout PNGs) and preview images
- `manifest.json`, `sw.js`: PWA install + offline cache
- `poster.html`, `make_qr.py`, `qr.svg`: printable classroom QR poster + generator
- `tools/`: art pipeline (see above)

## QR poster
Print `poster.html` (A4 portrait). The QR points at the live URL. If the repo is
ever renamed, regenerate the QR (`uv run --with qrcode python3 make_qr.py <url>`)
and reprint: old github.io URLs do not reliably redirect.
