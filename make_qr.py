#!/usr/bin/env python3
"""Generate the classroom poster QR code as a print-ready SVG file.

Usage:
    uv run --with qrcode python3 project/make_qr.py <url> [--out project/qr.svg]

Example (sanity check with a dummy URL):
    uv run --with qrcode python3 project/make_qr.py https://example.com

Colors match the poster and game palette:
    modules     #1A535C  (deep teal)
    background  #FDF6E3  (cream)

QR settings: error correction M (school posters get scuffed; M survives ~15%
damage), quiet zone of 4 modules (spec minimum), square modules, crisp edges.
"""
import argparse
from pathlib import Path

import qrcode

MODULE_FILL = "#1A535C"
BG_FILL = "#FDF6E3"
QUIET_ZONE = 4  # modules, QR spec minimum


def build_svg(url: str) -> str:
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=1,
        border=0,  # quiet zone added below so it is guaranteed symmetric
    )
    qr.add_data(url)
    qr.make(fit=True)
    modules = qr.modules  # rows of booleans, True = dark, no quiet zone

    width = len(modules[0]) + 2 * QUIET_ZONE
    height = len(modules) + 2 * QUIET_ZONE

    # Run-length encode each row into single rects: keeps the SVG small and
    # every module renders as an exact square under shape-rendering=crispEdges.
    rects = []
    for y, row in enumerate(modules):
        x = 0
        while x < len(row):
            if row[x]:
                run = 1
                while x + run < len(row) and row[x + run]:
                    run += 1
                rects.append(
                    f'<rect x="{x + QUIET_ZONE}" y="{y + QUIET_ZONE}" '
                    f'width="{run}" height="1"/>'
                )
                x += run
            else:
                x += 1

    body = "\n    ".join(rects)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" '
        f'width="{width * 12}" height="{height * 12}" '
        f'shape-rendering="crispEdges">\n'
        f'  <title>QR code for {url}</title>\n'
        f'  <rect width="{width}" height="{height}" fill="{BG_FILL}"/>\n'
        f'  <g fill="{MODULE_FILL}">\n    {body}\n  </g>\n'
        f'</svg>\n'
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the classroom poster QR code as SVG."
    )
    parser.add_argument("url", help="URL the QR code should open (the game link)")
    parser.add_argument(
        "--out",
        default="project/qr.svg",
        help="output SVG path (default: project/qr.svg)",
    )
    args = parser.parse_args()

    if not args.url.startswith(("http://", "https://")):
        parser.error("url must start with http:// or https://")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_svg(args.url), encoding="utf-8")
    print(f"Wrote {out} for {args.url}")


if __name__ == "__main__":
    main()
