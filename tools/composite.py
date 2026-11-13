#!/usr/bin/env python3
"""Composite classroom layers over the shell (and run alignment tests).

Slots are pixel boxes on the 1024x1024 canvas, tuned against base v3.
Usage:
  python3 composite.py all [bg]     composite every slot layer over bg (default shell.png)
  python3 composite.py fit NAME X Y W H   test-fit one layer at a manual box
Writes assets/_composite-test.png
"""
import sys
import pathlib
from PIL import Image

ASSETS = pathlib.Path(__file__).resolve().parent.parent / "assets"

# slot boxes: (x0, y0, x1, y1) on the 1024 canvas
SLOTS = {
    "old-window":   (110, 240, 235, 490),
    "blackboard":   (598, 270, 875, 555),
    "old-fan":      (415, 135, 515, 240),   # fit by fan head, top-aligned
    "clock":        (705, 150, 765, 215),
    "map":          (255, 255, 395, 430),
    "bookshelf":    (240, 435, 415, 620),
    "desks":        (255, 525, 745, 875),
    "teacher-desk": (580, 500, 755, 660),
    "rugs":         (785, 545, 915, 675),
    "plant":        (85, 605, 190, 725),
    # replacements and add-ons
    "fix-window":   (110, 240, 235, 490),
    "whiteboard":   (598, 270, 875, 555),
    "ac":           (395, 110, 545, 265),
    "tv":           (620, 130, 860, 265),
    "poster-english": (115, 500, 230, 615),
    "poster-map":   (255, 255, 395, 430),
    "kaligrafi":    (595, 145, 695, 250),
    "flag":         (880, 150, 965, 270),
    "papan-karya":  (880, 300, 965, 520),
    "curtains":     (105, 225, 240, 360),
    "plants-new":   (85, 605, 190, 725),
    "bookshelf-new": (240, 435, 415, 620),
    "rugs-new":     (785, 545, 915, 675),
}

# layers drawn over the shell in this order (back to front)
ORDER = [
    "old-window", "blackboard", "old-fan", "clock", "map",
    "bookshelf", "desks", "teacher-desk", "rugs", "plant",
]

BIG = ["wall-paint", "floor-tiles"]  # pasted unscaled at crop origin

FINAL = [
    "fix-window", "whiteboard", "ac", "poster-map", "bookshelf-new",
    "desks", "teacher-desk", "rugs-new", "plants-new", "curtains",
    "tv", "kaligrafi", "flag", "poster-english", "papan-karya",
]


def load_cut(name):
    p = ASSETS / (name + "-cut.png")
    s = Image.open(p).convert("RGBA")
    bb = s.split()[3].getbbox()
    return s.crop(bb)


def fit_paste(base, sprite, box, top_align=False):
    # extraction layers: width-fit at the slot origin (no cover overflow)
    x0, y0, x1, y1 = box
    scale = (x1 - x0) / sprite.width
    nw, nh = int(sprite.width * scale), int(sprite.height * scale)
    s = sprite.resize((nw, nh), Image.NEAREST)
    base.alpha_composite(s, (x0, y0))
    return (nw, nh, x0, y0)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode == "fit":
        name = sys.argv[2]
        x, y, w, h = (int(v) for v in sys.argv[3:7])
        base = Image.open(ASSETS / "shell.png").convert("RGBA")
        info = fit_paste(base, load_cut(name), (x, y, x + w, y + h))
        print(name, "->", info)
    else:
        bg = sys.argv[2] if len(sys.argv) > 2 else "shell.png"
        base = Image.open(ASSETS / bg).convert("RGBA")
        names = FINAL if mode == "final" else ORDER
        if mode == "final":
            for name in BIG:
                cut = ASSETS / (name + "-cut.png")
                if cut.exists():
                    s = Image.open(cut).convert("RGBA")
                    bb = s.split()[3].getbbox()
                    base.alpha_composite(s.crop(bb), (bb[0], bb[1]))
                    print(name, "-> big paste at", (bb[0], bb[1]))
        for name in names:
            cut = ASSETS / (name + "-cut.png")
            if not cut.exists():
                print("skip (missing):", name)
                continue
            info = fit_paste(base, load_cut(name), SLOTS[name], top_align=(name == "old-fan"))
            print(name, "->", info)
    out = ASSETS / "_composite-test.png"
    base.convert("RGB").save(out)
    print("saved", out)


if __name__ == "__main__":
    main()
