#!/usr/bin/env python3
"""Build the Portal-inspired 16:10 Hermes wallpaper.

Requires ImageMagick. The source engraving is CC BY 4.0; attribution lives in
NOTICE and README.md.
"""
from pathlib import Path
import math
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/source/mercury-hermes-frezza-1704.jpg"
OUTPUT = ROOT / "backgrounds/01-hermes-portal.png"
W, H = 3840, 2400


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def rays(cx: int, cy: int, inner: int, outer: int, count: int) -> str:
    lines = []
    for i in range(count):
        a = (2 * math.pi * i / count) + 0.015
        x1, y1 = cx + math.cos(a) * inner, cy + math.sin(a) * inner
        x2, y2 = cx + math.cos(a) * outer, cy + math.sin(a) * outer
        lines.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" '
            f'x2="{x2:.1f}" y2="{y2:.1f}"/>'
        )
    return "".join(lines)


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    figure_mask = td / "figure-mask.png"
    figure = td / "figure.png"
    figure_blue = td / "figure-blue.png"
    base_svg = td / "base.svg"
    base_png = td / "base.png"

    # Convert dark engraving ink into an alpha mask. Pale paper disappears;
    # crosshatching remains, preserving the Portal's etched/dithered character.
    run(
        "magick", str(SOURCE),
        "-crop", "2420x3400+130+120", "+repage",
        "-colorspace", "Gray",
        "-negate",
        "-contrast-stretch", "1%x1%",
        "-threshold", "55%",
        "-resize", "1820x2380!",
        str(figure_mask),
    )
    run(
        "magick", "-size", "1820x2380", "xc:#F5F5F5",
        str(figure_mask), "-alpha", "off", "-compose", "CopyOpacity",
        "-composite", str(figure),
    )
    run(
        "magick", "-size", "1820x2380", "xc:#5B6CFF",
        str(figure_mask), "-alpha", "off", "-compose", "CopyOpacity",
        "-composite", "-channel", "A", "-evaluate", "multiply", "0.36",
        "+channel", str(figure_blue),
    )

    ray_markup = rays(3030, 870, 430, 1170, 104)
    base_svg.write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="stage" x1="0" x2="1"><stop stop-color="#09091A"/><stop offset="1" stop-color="#11112B"/></linearGradient>
  <radialGradient id="blueglow"><stop stop-color="#0000F2" stop-opacity=".28"/><stop offset="1" stop-color="#0000F2" stop-opacity="0"/></radialGradient>
  <pattern id="dots" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.5" fill="#F5F5F5" opacity=".08"/></pattern>
  <pattern id="grid" width="80" height="80" patternUnits="userSpaceOnUse"><path d="M80 0H0V80" fill="none" stroke="#F5F5F5" stroke-opacity=".025"/></pattern>
</defs>
<rect width="3840" height="2400" fill="#070716"/>
<rect x="0" y="0" width="2260" height="2400" fill="url(#stage)"/>
<rect x="2260" y="0" width="1580" height="2400" fill="#0B0B20"/>
<rect width="3840" height="2400" fill="url(#grid)"/>
<rect x="2400" y="80" width="1360" height="2240" fill="none" stroke="#34345A" stroke-width="3"/>
<circle cx="3030" cy="870" r="1220" fill="url(#blueglow)"/>
<g stroke="#5B6CFF" stroke-width="2.4" opacity=".34">{ray_markup}</g>
<g opacity=".9">
  <path d="M0 150H2130M0 2250H2130" stroke="#34345A" stroke-width="2"/>
  <path d="M2130 0V2400M2260 0V2400" stroke="#0000F2" stroke-width="3"/>
</g>
<rect x="120" y="118" width="1180" height="52" fill="url(#dots)" opacity=".75"/>
<g font-family="DejaVu Sans Mono,monospace" letter-spacing="6">
  <text x="120" y="108" fill="#EDFF45" font-size="24">// NOUS RESEARCH</text>
  <text x="1880" y="108" fill="#8C8CA7" font-size="20" text-anchor="end">AGENT SYSTEM 01</text>
  <text x="120" y="1980" fill="#8C8CA7" font-size="22">CONNECT · REMEMBER · SCHEDULE · DELEGATE</text>
  <text x="3670" y="2280" fill="#8C8CA7" font-size="18" text-anchor="end">MERCVRIVS // 1704</text>
</g>
<g fill="#F5F5F5" font-family="DejaVu Serif,serif">
  <text x="120" y="1630" font-size="220" letter-spacing="12">HERMES</text>
  <text x="120" y="1840" font-size="220" letter-spacing="12">AGENT</text>
</g>
<rect x="120" y="1910" width="620" height="12" fill="#0000F2"/>
<rect x="740" y="1910" width="160" height="12" fill="#EDFF45"/>
<g font-family="DejaVu Sans Mono,monospace" font-size="18" fill="#5B6CFF" opacity=".8">
  <text x="2390" y="150">#01</text><text x="3660" y="150" text-anchor="end">PORTAL_</text>
</g>
</svg>''')

    run("rsvg-convert", "-w", str(W), "-h", str(H), str(base_svg), "-o", str(base_png))
    # Blue offset print-registration shadow, then paper-white engraving.
    run(
        "magick", str(base_png),
        str(figure_blue), "-geometry", "+2070+35", "-compose", "over", "-composite",
        str(figure), "-geometry", "+2042+15", "-compose", "over", "-composite",
        "-strip", str(OUTPUT),
    )

print(f"generated {OUTPUT} ({W}x{H})")
