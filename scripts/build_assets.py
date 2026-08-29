#!/usr/bin/env python3
"""Build original Hermarchy command-environment artwork."""
from pathlib import Path
import math
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/source"
BACKGROUNDS = ROOT / "backgrounds"
W, H = 3840, 2400
FLAGSHIP_SOURCE_CENTER_Y = 1050
FLAGSHIP_VERTICAL_SHIFT = H // 2 - FLAGSHIP_SOURCE_CENTER_Y
SOURCE.mkdir(parents=True, exist_ok=True)
BACKGROUNDS.mkdir(parents=True, exist_ok=True)

BG = "#08090A"
SURFACE = "#101214"
BORDER = "#272B2F"
WHITE = "#F1F1EC"
SECONDARY = "#9B9E9F"
MUTED = "#606468"
CYAN = "#61D6FF"
BRIGHT = "#8DE4FF"


def lines(cx: int, cy: int, inner: int, outer: int, count: int, color: str, opacity: float) -> str:
    result = []
    for i in range(count):
        a = 2 * math.pi * i / count
        result.append(
            f'<line x1="{cx + math.cos(a)*inner:.1f}" y1="{cy + math.sin(a)*inner:.1f}" '
            f'x2="{cx + math.cos(a)*outer:.1f}" y2="{cy + math.sin(a)*outer:.1f}"/>'
        )
    return f'<g stroke="{color}" stroke-width="2" opacity="{opacity}">' + "".join(result) + "</g>"


def frame() -> str:
    return f'''
<rect width="{W}" height="{H}" fill="{BG}"/>
<path d="M80 128H3760M80 2272H3760" stroke="{BORDER}" stroke-width="2"/>
<path d="M128 80V2320M3712 80V2320" stroke="{BORDER}" stroke-width="2"/>
<g fill="{MUTED}" font-family="IBM Plex Mono,JetBrains Mono,DejaVu Sans Mono,monospace" font-size="19" letter-spacing="5">
 <text x="108" y="112">HERMARCHY</text>
 <text x="3732" y="112" text-anchor="end">AGENT ENVIRONMENT 01</text>
</g>
<circle cx="3660" cy="105" r="5" fill="{CYAN}"/>
'''


def wallpaper_one() -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
 <pattern id="grid" width="96" height="96" patternUnits="userSpaceOnUse"><path d="M96 0H0V96" fill="none" stroke="{WHITE}" stroke-opacity=".018"/></pattern>
 <radialGradient id="halo"><stop stop-color="{CYAN}" stop-opacity=".055"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>
</defs>
{frame()}
<rect x="128" y="128" width="3584" height="2144" fill="url(#grid)"/>
<g transform="translate(0 {FLAGSHIP_VERTICAL_SHIFT})">
<circle cx="1920" cy="{FLAGSHIP_SOURCE_CENTER_Y}" r="980" fill="url(#halo)"/>
{lines(1920,FLAGSHIP_SOURCE_CENTER_Y,370,940,96,CYAN,.045)}
<g text-anchor="middle">
 <text x="1920" y="925" fill="{WHITE}" font-family="IBM Plex Sans,Inter,DejaVu Sans,sans-serif" font-size="186" font-weight="500" letter-spacing="54">HERMARCHY</text>
 <text x="1920" y="1055" fill="{CYAN}" font-family="IBM Plex Mono,JetBrains Mono,DejaVu Sans Mono,monospace" font-size="36" letter-spacing="18">/\\-_=+|&lt; -/= ~:*-/</text>
 <text x="1920" y="1195" fill="{SECONDARY}" font-family="IBM Plex Mono,JetBrains Mono,DejaVu Sans Mono,monospace" font-size="26" letter-spacing="12">AGENT ENVIRONMENT</text>
 <text x="1920" y="1250" fill="{MUTED}" font-family="IBM Plex Mono,JetBrains Mono,DejaVu Sans Mono,monospace" font-size="20" letter-spacing="10">OMARCHY AGENT THEME</text>
</g>
</g>
<g font-family="IBM Plex Mono,JetBrains Mono,DejaVu Sans Mono,monospace" font-size="21" letter-spacing="4">
 <text x="170" y="1850" fill="{CYAN}">HERMARCHY::NODE</text>
 <text x="170" y="1900" fill="{MUTED}">STATE</text><text x="380" y="1900" fill="{WHITE}">READY</text>
 <text x="170" y="1950" fill="{MUTED}">HOST</text><text x="380" y="1950" fill="{WHITE}">OMARCHY</text>
 <text x="170" y="2000" fill="{MUTED}">MODE</text><text x="380" y="2000" fill="{WHITE}">LOCAL</text>
 <text x="3670" y="1940" fill="{WHITE}" text-anchor="end">HERMARCHY</text>
 <text x="3670" y="1990" fill="{MUTED}" text-anchor="end">LOCAL AGENT ENVIRONMENT</text>
</g>
</svg>'''


def node_markup() -> str:
    pts = [(2540,540),(3000,420),(3390,700),(3240,1130),(3490,1540),(2990,1840),(2520,1630),(2360,1180),(2780,990),(3050,1310)]
    edges = [(0,1),(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,0),(0,8),(8,1),(8,9),(9,3),(9,5),(9,6)]
    e = "".join(f'<line x1="{pts[a][0]}" y1="{pts[a][1]}" x2="{pts[b][0]}" y2="{pts[b][1]}"/>' for a,b in edges)
    n = "".join(f'<circle cx="{x}" cy="{y}" r="{9 if i not in (8,9) else 15}"/>' for i,(x,y) in enumerate(pts))
    return f'<g stroke="{CYAN}" stroke-width="2" opacity=".22">{e}</g><g fill="{BG}" stroke="{CYAN}" stroke-width="3" opacity=".72">{n}</g>'


def wallpaper_two() -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
{frame()}
{lines(2920,1120,260,1120,120,WHITE,.026)}
{node_markup()}
<g font-family="IBM Plex Mono,JetBrains Mono,DejaVu Sans Mono,monospace">
 <text x="190" y="520" fill="{CYAN}" font-size="25" letter-spacing="7">// ROUTING MAP</text>
 <text x="190" y="760" fill="{WHITE}" font-size="116" letter-spacing="20">HERMARCHY</text>
 <text x="190" y="880" fill="{WHITE}" font-size="116" letter-spacing="25">NODE</text>
 <path d="M190 950H1180" stroke="{BORDER}" stroke-width="2"/><path d="M190 950H480" stroke="{CYAN}" stroke-width="3"/>
 <text x="190" y="1050" fill="{MUTED}" font-size="22" letter-spacing="5">LOCAL AGENT CONTROL PLANE</text>
 <text x="190" y="1990" fill="{MUTED}" font-size="20">01  HUMAN INPUT</text>
 <text x="190" y="2040" fill="{MUTED}" font-size="20">02  SYSTEM ROUTING</text>
 <text x="190" y="2090" fill="{CYAN}" font-size="20">03  AGENT EXECUTION  ● READY</text>
</g>
</svg>'''


def wallpaper_three() -> str:
    rows = [
        ("01", "CONNECT", "MODEL PROVIDERS AND REMOTE NODES"),
        ("02", "REMEMBER", "PERSISTENT CONTEXT AND USER MEMORY"),
        ("03", "SCHEDULE", "AUTONOMOUS AND RECURRING OPERATIONS"),
        ("04", "DELEGATE", "PARALLEL SPECIALIST AGENT WORKFLOWS"),
    ]
    markup = []
    for i,(n,title,desc) in enumerate(rows):
        y = 690 + i*300
        markup.append(f'''<g font-family="IBM Plex Mono,JetBrains Mono,DejaVu Sans Mono,monospace">
 <text x="300" y="{y}" fill="{CYAN}" font-size="25">[{n}]</text>
 <text x="520" y="{y}" fill="{WHITE}" font-size="72" letter-spacing="12">{title}</text>
 <text x="2060" y="{y}" fill="{MUTED}" font-size="21" letter-spacing="4">{desc}</text>
 <path d="M300 {y+72}H3540" stroke="{BORDER}" stroke-width="2"/>
</g>''')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
{frame()}
<text x="300" y="360" fill="{WHITE}" font-family="IBM Plex Sans,Inter,DejaVu Sans,sans-serif" font-size="132" letter-spacing="28">CAPABILITIES</text>
<text x="3510" y="360" text-anchor="end" fill="{CYAN}" font-family="IBM Plex Mono,monospace" font-size="24" letter-spacing="6">SYSTEM ONLINE ●</text>
{''.join(markup)}
</svg>'''


wallpapers = [wallpaper_one(), wallpaper_two(), wallpaper_three()]
for index, svg in enumerate(wallpapers, 1):
    source = SOURCE / f"hermarchy-{index}.svg"
    output = BACKGROUNDS / ("01-hermarchy-command.png" if index == 1 else f"hermarchy-{index}.png")
    source.write_text(svg)
    subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), str(source), "-o", str(output)], check=True)

unlock = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="288" viewBox="0 0 1024 288">
<text x="512" y="112" fill="{WHITE}" text-anchor="middle" font-family="IBM Plex Sans,Inter,DejaVu Sans,sans-serif" font-size="76" letter-spacing="20">HERMARCHY</text>
<text x="512" y="178" fill="{CYAN}" text-anchor="middle" font-family="IBM Plex Mono,DejaVu Sans Mono,monospace" font-size="24" letter-spacing="10">/\\-_=+|&lt; -/= ~:*-/</text>
<text x="512" y="238" fill="{MUTED}" text-anchor="middle" font-family="IBM Plex Mono,DejaVu Sans Mono,monospace" font-size="15" letter-spacing="7">NODE LOCKED // AUTHENTICATE</text>
</svg>'''
(SOURCE / "unlock.svg").write_text(unlock)
subprocess.run(["rsvg-convert", "-w", "1024", "-h", "288", str(SOURCE / "unlock.svg"), "-o", str(ROOT / "unlock.png")], check=True)
print("generated", *(str(p) for p in sorted(BACKGROUNDS.glob("*.png"))))
