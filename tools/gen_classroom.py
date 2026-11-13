#!/usr/bin/env python3
"""Classroom art pipeline: Nano Banana 2.1 via Agent Platform REST (gcloud ADC).

Usage:
  python3 gen_classroom.py <name> [prompt] [ref.png ...]
Known prompt keys use built-in prompts (extra args = reference images).
Otherwise pass the prompt as the second argument.
Writes project/word-rain/assets/<name>.png
"""
import base64
import json
import pathlib
import subprocess
import sys
import time
import urllib.request

PROJECT = "finishyourgame"
MODEL = "gemini-nano-banana-2.1"
URL = ("https://aiplatform.googleapis.com/v1/projects/" + PROJECT +
       "/locations/global/publishers/google/models/" + MODEL + ":generateContent")
OUT = pathlib.Path(__file__).resolve().parent.parent / "assets"

STYLE = ("16-bit pixel art, 45-degree isometric room-box style (Habbo-like dollhouse), "
         "thick clean outlines, "
         "limited warm palette: cream walls, teal accents, warm wood browns, "
         "soft ambient shadows, dithered shading, no text, no letters, no numbers, "
         "no people, no watermark.")

PROMPTS = {
    "base": (
        "Isometric pixel art classroom in a cutaway room box with open top, viewed at a "
        "45-degree high angle like a miniature dollhouse. Two back walls meet at a vertical "
        "corner in the center back. Left wall: tall window with cracked broken glass panes, "
        "a map poster, a dim wall-mounted fan. Right wall: a large old dark blackboard, "
        "slightly crooked, with a wall clock above it. "
        "Cream walls with peeling paint patches and bare nail holes, plain painted walls "
        "from floor to top with no wood paneling, no wainscoting, no wood trim on walls. Floor: "
        "teal grid tiles, dusty and scuffed. Small wooden student desks with chairs in rows "
        "facing the blackboard, one teacher desk with a chair near the blackboard, a low "
        "bookshelf along the left wall, a potted plant in the front corner, a stack of rugs "
        "in another corner. Mood: tired and quiet, waiting to be repaired. " + STYLE
    ),
    "fix-window": (
        "Using the attached classroom image ONLY as reference for exact position, size, "
        "isometric angle and pixel-art style. Draw ONLY a single flat window seen at the exact "
        "isometric tilt of the left-wall window in the reference: ONE window plane only, wooden "
        "frame, clean intact glass panes, TALL and NARROW like that window: about twice as tall "
        "as it is wide, 2 panes wide and 3 panes tall, same silhouette and footprint as that "
        "window. NOT a "
        "corner unit, NOT freestanding, no second window face, no floor plinth, no sill below. "
        "Isolated on a plain pure white background. No walls, no room, nothing else. " + STYLE
    ),
    "whiteboard": (
        "Using the attached classroom image ONLY as reference for exact position, size, "
        "isometric angle and pixel-art style. Draw ONLY a white whiteboard with a marker tray "
        "that FULLY COVERS the blackboard from the reference: exact same width and height as the "
        "blackboard including its frame area, same isometric tilt, same wall plane, so it can be "
        "pasted directly over the blackboard. Isolated on a plain pure white background, no "
        "walls, no other objects, nothing else. " + STYLE
    ),
    "shell": (
        "Using the attached classroom as exact reference for geometry, perspective and "
        "style: the SAME isometric room box but COMPLETELY EMPTY. Same cream walls with "
        "peeling paint patches, same teal scuffed floor tiles, same wall corner and open "
        "top, same lighting. NO objects at all: no window opening, no fan, no blackboard, "
        "no clock, no posters, no furniture, no rugs, no plant, nothing on walls or floor. "
        "Plain walls and plain floor only. " + STYLE
    ),
    "old-fan": (
        "Using the attached classroom image ONLY as reference for exact position, size, "
        "isometric angle and pixel-art style. Draw ONLY the old worn dim wall-mounted fan "
        "exactly as it appears in the reference: same dusty brown fan, same cage, same "
        "isometric angle, isolated on a plain pure white background. No wall, no room, "
        "nothing else. " + STYLE
    ),
    "ac": (
        "Using the attached classroom image ONLY as reference for exact position, size, "
        "isometric angle and pixel-art style. Draw ONLY a modern white wall-mounted air "
        "conditioner unit, sized to replace the old wall fan from the reference, same "
        "isometric angle, isolated on a plain pure white background. No walls, no floor, no "
        "room, no other objects, nothing else. " + STYLE
    ),
    "old-window": (
        "Using the attached classroom image ONLY as reference for exact position, size, "
        "isometric angle and pixel-art style. Draw ONLY the old broken window exactly as it "
        "appears in the reference: tall narrow wooden window, 2 panes wide and 3 panes tall, "
        "cracked glass with holes, worn frame. ONE window plane only, same isometric tilt. "
        "Isolated on a plain pure white background. No wall, no room, nothing else. " + STYLE
    ),
    "blackboard": (
        "Using the attached classroom image ONLY as reference for exact position, size, "
        "isometric angle and pixel-art style. Draw ONLY the old dark blackboard exactly as it "
        "appears in the reference: large, slightly crooked, worn wooden frame, faint chalk "
        "smudges, same size and same isometric tilt as the reference blackboard. Isolated on "
        "a plain pure white background. No wall, no room, nothing else. " + STYLE
    ),
    "clock": (
        "Using the attached classroom image ONLY as reference for exact position, size, "
        "isometric angle and pixel-art style. Draw ONLY the old wall clock exactly as it "
        "appears in the reference: round clock with simple face and hands. Isolated on a "
        "plain pure white background. No wall, no room, nothing else. " + STYLE
    ),
    "map": (
        "Using the attached classroom image ONLY as reference for exact position, size, "
        "isometric angle and pixel-art style. Draw ONLY the worn world map poster exactly as "
        "it appears in the reference: LARGE square-ish poster, about as tall as it is wide "
        "(or slightly taller), the same prominent size as the reference map, slightly torn "
        "corners, same isometric tilt. Isolated on a plain pure white background. No wall, no "
        "room, nothing else. " + STYLE
    ),
    "bookshelf": (
        "Using the attached classroom image ONLY as reference for exact position, size, "
        "isometric angle and pixel-art style. Draw ONLY the low wooden bookshelf with books "
        "exactly as it appears in the reference: same size, same isometric angle. Isolated on "
        "a plain pure white background. No wall, no floor, no room, nothing else. " + STYLE
    ),
    "desks": (
        "Using the attached classroom image ONLY as reference for exact position, size, "
        "isometric angle and pixel-art style. Draw ONLY the whole group of wooden student "
        "desks with chairs exactly as arranged in the reference: all desks in one group "
        "keeping their relative arrangement, same isometric angle. Isolated on a plain pure "
        "white background. No floor, no room, nothing else. " + STYLE
    ),
    "teacher-desk": (
        "Using the attached classroom image ONLY as reference for exact position, size, "
        "isometric angle and pixel-art style. Draw ONLY the teacher desk with papers on top "
        "and its chair exactly as it appears in the reference: same size, same isometric "
        "angle. Isolated on a plain pure white background. No floor, no room, nothing else. " + STYLE
    ),
    "rugs": (
        "Using the attached classroom image ONLY as reference for exact position, size, "
        "isometric angle and pixel-art style. Draw ONLY the stack of rolled rugs and mats in "
        "the corner exactly as it appears in the reference: same size, same isometric angle. "
        "Isolated on a plain pure white background. No floor, no wall, no room, nothing "
        "else. " + STYLE
    ),
    "plant": (
        "Using the attached classroom image ONLY as reference for exact position, size, "
        "isometric angle and pixel-art style. Draw ONLY the potted plant with drooping leaves "
        "exactly as it appears in the reference: same pot, same size, same isometric angle. "
        "Isolated on a plain pure white background. No floor, no room, nothing else. " + STYLE
    ),
    "tv": (
        "Using the attached classroom image ONLY as reference for size, isometric angle and "
        "pixel-art style. Draw ONLY a modern flat-screen TV on a small wall mount bracket, "
        "seen at the same isometric tilt as the reference blackboard (it will hang above the "
        "blackboard). Isolated on a plain pure white background. No wall, no room, nothing "
        "else. " + STYLE
    ),
    "poster-english": (
        "Using the attached classroom image ONLY as reference for size, isometric angle and "
        "pixel-art style. Draw ONLY a colorful classroom learning poster showing simple "
        "pictures of everyday objects (an apple, a ball, a cat, a book) in a neat grid with a "
        "thin border, same isometric tilt as the reference map poster. Isolated on a plain "
        "pure white background. No wall, no room, nothing else. " + STYLE
    ),
    "poster-map": (
        "Using the attached classroom image ONLY as reference for exact size and isometric "
        "angle. Draw ONLY a NEW crisp clean world map poster (oceans in blue, continents in "
        "green and tan), same size and same isometric tilt as the worn map in the reference, "
        "straight untorn edges. Isolated on a plain pure white background. No wall, no room, "
        "nothing else. " + STYLE
    ),
    "kaligrafi": (
        "Using the attached classroom image ONLY as reference for size, isometric angle and "
        "pixel-art style. Draw ONLY a square Islamic geometric pattern wall decoration: "
        "interlocking eight-point star and polygon tiles in teal, gold and cream, thin frame, "
        "same wall tilt as the reference posters. Strictly NO letters, NO writing, NO script "
        "of any kind, pure geometry only. Isolated on a plain pure white background. No wall, "
        "no room, nothing else. " + STYLE
    ),
    "flag": (
        "Using the attached classroom image ONLY as reference for size, isometric angle and "
        "pixel-art style. Draw ONLY a small Indonesian flag (horizontal red band above white "
        "band) mounted on a short wooden wall pole, same wall tilt as the reference posters. "
        "Isolated on a plain pure white background. No wall, no room, nothing else. " + STYLE
    ),
    "papan-karya": (
        "Using the attached classroom image ONLY as reference for size, isometric angle and "
        "pixel-art style. Draw ONLY a wooden-framed display board with several small colorful "
        "children's drawings pinned on it (abstract shapes, suns, houses), same wall tilt as "
        "the reference posters. Isolated on a plain pure white background. No wall, no room, "
        "nothing else. " + STYLE
    ),
    "curtains": (
        "Using the attached classroom image ONLY as reference for exact size and isometric "
        "angle. Draw ONLY a pair of simple cream curtains on a slim wooden rod, sized to sit "
        "over the top half of the reference window, same isometric tilt as the window. "
        "Isolated on a plain pure white background. No wall, no window, no room, nothing "
        "else. " + STYLE
    ),
    "clock-new": (
        "Using the attached classroom image ONLY as reference for exact size and isometric "
        "angle. Draw ONLY a NEW modern round wall clock (clean white face, clear hands), "
        "exactly the same size as the old clock in the reference. Isolated on a plain pure "
        "white background. No wall, no room, nothing else. " + STYLE
    ),
    "plants-new": (
        "Using the attached classroom image ONLY as reference for exact size and isometric "
        "angle. Draw ONLY a HEALTHY vibrant potted plant with lush green leaves in a "
        "terracotta pot, exactly the same pot size as the drooping plant in the reference. "
        "Isolated on a plain pure white background. No floor, no room, nothing else. " + STYLE
    ),
    "bookshelf-new": (
        "Using the attached classroom image ONLY as reference for exact size and isometric "
        "angle. Draw ONLY a NEW tidy wooden bookshelf with neatly arranged colorful books and "
        "a few items on top, exactly the same size and shape as the old bookshelf in the "
        "reference. Isolated on a plain pure white background. No wall, no floor, no room, "
        "nothing else. " + STYLE
    ),
    "rugs-new": (
        "Using the attached classroom image ONLY as reference for exact size and isometric "
        "angle. Draw ONLY a NEAT stack of folded prayer rugs (patterned green and red "
        "fabrics), same overall size as the rolled rug pile in the reference corner. "
        "Isolated on a plain pure white background. No floor, no wall, no room, nothing "
        "else. " + STYLE
    ),
    "shell-base": (
        "Using the attached classroom as exact reference for geometry, size and "
        "perspective: the SAME isometric room box STRUCTURE ONLY, with completely plain "
        "neutral gray walls and a plain neutral gray floor. No paint texture, no peeling, "
        "no tiles, no scuffs, no objects, no window, nothing on the surfaces. Only the "
        "room box structure: wall corner, top rim, floor rim, clean thick outlines. "
        "16-bit pixel art, no text, no people, no watermark. Isolated on a plain pure "
        "white background."
    ),
    "old-wall": (
        "Using the attached classroom image ONLY as reference for exact geometry and size: "
        "the OLD wall surfaces exactly as in the reference: the two back wall faces with "
        "peeling cream paint patches and bare nail holes, same shape and position. "
        "Isolated on a plain pure white background. Only the wall surfaces: no floor, no "
        "rim, no objects, nothing else. " + STYLE
    ),
    "old-floor": (
        "Using the attached classroom image ONLY as reference for exact geometry and size: "
        "the OLD floor surface exactly as in the reference: the diamond floor with scuffed "
        "worn teal grid tiles, same shape and position. Isolated on a plain pure white "
        "background. Only the floor surface: no walls, no rim, no objects, nothing else. " + STYLE
    ),
}


def token():
    return subprocess.check_output(
        ["gcloud", "auth", "application-default", "print-access-token"],
        text=True).strip()


def generate(name, prompt, refs):
    parts = [{"text": prompt}]
    for ref in refs:
        parts.append({"inline_data": {
            "mime_type": "image/png",
            "data": base64.b64encode(pathlib.Path(ref).read_bytes()).decode()}})
    body = {
        "contents": [{"role": "user", "parts": parts}],
        "generation_config": {
            "response_modalities": ["TEXT", "IMAGE"],
            "image_config": {"aspect_ratio": "1:1", "image_size": "1K"},
            "thinking_config": {"thinking_level": "MEDIUM", "include_thoughts": False},
        },
    }
    for attempt in range(5):
        try:
            req = urllib.request.Request(
                URL, data=json.dumps(body).encode(), method="POST",
                headers={"Authorization": "Bearer " + token(),
                         "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                resp = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 4:
                wait = 30 * (attempt + 1)
                print("429 rate-limited, waiting", wait, "s...")
                time.sleep(wait)
            else:
                raise
    for cand in resp.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            data = part.get("inlineData") or part.get("inline_data") or {}
            if data.get("data"):
                OUT.mkdir(parents=True, exist_ok=True)
                out = OUT / (name + ".png")
                out.write_bytes(base64.b64decode(data["data"]))
                print("OK", out, out.stat().st_size, "bytes")
                return
    raise SystemExit("no image in response: " + json.dumps(resp)[:500])


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "base"
    if name in PROMPTS:
        prompt, rest = PROMPTS[name], sys.argv[2:]
    elif len(sys.argv) > 2:
        prompt, rest = sys.argv[2], sys.argv[3:]
    else:
        raise SystemExit("usage: gen_classroom.py <name> [prompt] [ref.png ...]")
    generate(name, prompt, rest)
