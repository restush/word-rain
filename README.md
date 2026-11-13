# Temp: Word Rain (Grade 3 English)

A lightweight portrait browser game for Grade 3 English (Fase B). Vocabulary words fall down the screen and students tap the right ones. Vanilla JS, one file, no dependencies, works offline after the first load.

**Play: https://restush.github.io/temp/**

## Update the word list

Edit the `CONTENT` table at the top of the `<script>` block in `index.html`:
`en` = English word, `id` = bahasa Indonesia, `pic` = emoji or `#color`, `tag` = `animal` or `color`.
Commit and push; GitHub Pages redeploys in about a minute.

## QR poster

1. `poster.html` is the printable A4 classroom poster. Replace `{{GAME_NAME}}` before printing.
2. Regenerate the QR code: `uv run --with qrcode python3 make_qr.py https://restush.github.io/temp/`
3. Print A4 portrait, margins none. If this repo is ever renamed, the URL changes: regenerate the QR and reprint posters.

## Structure

- `index.html` — the game (teachers edit only the CONTENT table)
- `poster.html` — classroom QR poster template
- `make_qr.py` — QR generator (writes `qr.svg`)
