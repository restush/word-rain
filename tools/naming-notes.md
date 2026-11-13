# Naming Notes: game codename "Temp" to final public name

Context: falling-vocabulary tap game for Grade 3 English (Fase B) at SDIT Baitussalam 2
Cangkringan (JSIT). Kids scan a QR poster with Android phones; the teacher says the name out
loud in class ("scan the [NAME] poster"). Meta layer: earn coins, renovate a pixel classroom.
Poster template holds a {{GAME_NAME}} placeholder. Scores weigh: short QR-friendly slug
(a-z0-9-hyphen), pronounceability for an Indonesian teacher, kid memorability (age 8-9),
wholesome Islamic-school fit, word/English/learning hints, brand collision safety.

## Candidates

| # | Name | Slug | Why it fits | Risks |
|---|------|------|-------------|-------|
| 1 | Word Rain | word-rain | Concept name already used in project notes; falling-words metaphor kids can picture; English wordmark signals the subject | Two English words for the teacher to say; generic phrasing, tiny unknown apps may share it |
| 2 | Hujan Kata | hujan-kata | Natural Indonesian equivalent; effortless for teacher and kids; wholesome and poetic | Does not signal "English"; could be any language game |
| 3 | Kelas Kata | kelas-kata | Alliterative; "kelas" ties into the classroom renovation meta; school-warm | No falling-mechanic or English hint |
| 4 | Ruang Kata | ruang-kata | "Word room" also ties to the renovation meta; calm and wholesome | Same as above; slightly plain |
| 5 | Tepuk Kata | tepuk-kata | Action verb matches tapping; very Indonesian | "Tepuk" reads as clap (tepuk tangan), kids may expect clapping |
| 6 | Tangkap Kata | tangkap-kata | "Catch the words" matches the falling/catching feel | Longer slug (12 chars), denser QR |
| 7 | Word Pop | word-pop | Shortest slug here (8 chars); matches the pop sound/animation | "Pop" is English jargon; more small-game name crowding |
| 8 | Tap Kata | tap-kata | Short (8 chars); "tap" is universal kid vocabulary | Generic; weak English-learning hint |
| 9 | Kata Juara | kata-juara | Motivational, wholesome | Generic; no mechanic or subject hint |
| 10 | Kata Pintar | kata-pintar | "Smart words" reads as learning instantly | Plain; possible minor overlap with Indonesian edutainment titles |
| 11 | Tebak Kata | tebak-kata | Guessing framing is familiar | Crowded space, many Indonesian quiz games and shows use it |
| 12 | Kata Kita | kata-kita | "Our words" feels communal and school-warm | No subject or mechanic hint |

## Top 3 shortlist

1. **Word Rain** (word-rain): strongest overall, concept name, subject signal, short slug.
2. **Hujan Kata** (hujan-kata): safest for pronunciation and kid recall.
3. **Kelas Kata** (kelas-kata): best tie-in to the classroom renovation meta.

## Final recommendation

**Display name "Word Rain", slug `word-rain`, with "Hujan Kata" as the Indonesian subtitle on
the poster.** The name is already the established concept name in project notes, the falling
words metaphor is instantly imaginable for 8-9 year olds, and the English wordmark doubles as
a subject cue that this is an English game. The 9-character slug keeps QR density low for
cheap phone cameras, and the bilingual pairing gives the teacher a natural phrase: "scan the
Word Rain poster, itu Hujan Kata".

## QR and rename checklist

1. Confirm the name with Restu and the kepsek before anything else.
2. Rename the GitHub repo: repo Settings, General, Repository name, change "temp" to the slug. The Pages URL follows the repo name automatically.
3. Fix local links: `git remote set-url origin https://github.com/restush/<slug>.git`, update the vault `.gitmodules` URL and run `git submodule sync`, and rename the local folder `project/temp` to `project/<slug>` (the project/{gamename} convention).
4. Update display strings: `manifest.json` name/short_name, `poster.html` {{GAME_NAME}}, README titles.
5. Verify https://restush.github.io/<slug>/ serves the game (HTTP 200).
6. Regenerate the QR: `uv run --with qrcode python3 make_qr.py https://restush.github.io/<slug>/`.
7. THE TRAP: already-printed QR codes break after a repo rename, because old github.io Pages URLs do not reliably redirect. Rename first, print last, never the other way around.
8. Print sizing (A4 classroom poster): QR at least 4 cm square, 5-6 cm is better for wall scanning; keep the quiet zone (blank border, at least 4 modules wide, never crop or decorate it); dark code on light background (teal on cream passes); test-scan a printed proof from 1-2 meters with two different cheap Android phones before mass printing.
