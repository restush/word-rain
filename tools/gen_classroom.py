#!/usr/bin/env python3
"""Classroom art pipeline: Nano Banana 2.1 via Agent Platform REST (gcloud ADC).

Usage:
  python3 gen_classroom.py <name> [prompt] [ref.png ...]
Known prompt keys use built-in prompts (extra args = reference images).
Otherwise pass the prompt as the second argument.
Writes project/temp/assets/<name>.png
"""
import base64
import json
import pathlib
import subprocess
import sys
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
    req = urllib.request.Request(
        URL, data=json.dumps(body).encode(), method="POST",
        headers={"Authorization": "Bearer " + token(),
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        resp = json.load(r)
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
