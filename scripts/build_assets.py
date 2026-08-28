#!/usr/bin/env python3
"""Generate original Hermes/Nous wallpaper and gallery preview assets."""
from pathlib import Path
import math

ROOT = Path(__file__).resolve().parents[1]
BG = ROOT / "backgrounds"
SOURCE = ROOT / "assets" / "source"
BG.mkdir(parents=True, exist_ok=True)
SOURCE.mkdir(parents=True, exist_ok=True)

W, H = 3840, 2160

def rays(cx, cy, radius, count, color, opacity, phase: float = 0.0):
    out=[]
    for i in range(count):
        a=phase + i*2*math.pi/count
        inner=radius*0.42
        x1=cx+math.cos(a)*inner; y1=cy+math.sin(a)*inner
        x2=cx+math.cos(a)*radius; y2=cy+math.sin(a)*radius
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
    return f'<g stroke="{color}" stroke-width="2" opacity="{opacity}">' + ''.join(out) + '</g>'

def nodes(cx, cy):
    pts=[(-520,-290),(-300,-500),(0,-610),(330,-460),(560,-180),(510,190),(260,470),(-80,570),(-390,390),(-590,70),(-250,-100),(230,-140),(150,210),(-180,240)]
    links=[(0,1),(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,9),(9,0),(0,10),(10,11),(11,4),(10,13),(13,12),(12,11),(13,8),(12,6)]
    lines=''.join(f'<line x1="{cx+pts[a][0]}" y1="{cy+pts[a][1]}" x2="{cx+pts[b][0]}" y2="{cy+pts[b][1]}"/>' for a,b in links)
    circles=''.join(f'<circle cx="{cx+x}" cy="{cy+y}" r="{9 if i<10 else 13}"/>' for i,(x,y) in enumerate(pts))
    return f'<g stroke="#5B6CFF" stroke-width="3" fill="#09091A">{lines}{circles}</g>'

def wallpaper(variant):
    if variant==1:
        title, sub = "HERMES", "THE AGENT THAT GROWS WITH YOU"
        cx,cy=2670,1080
    elif variant==2:
        title, sub = "NOUS // HERMES", "ONE AGENT · ONE MEMORY · EVERY SURFACE"
        cx,cy=1920,1080
    else:
        title, sub = "HERMES // 03", "CONNECT · REMEMBER · SCHEDULE · DELEGATE"
        cx,cy=1200,1080
    align = 'start' if variant==1 else ('middle' if variant==2 else 'end')
    tx = 300 if variant==1 else (1920 if variant==2 else 3540)
    graphic = f'''{rays(cx,cy,820,96,"#5B6CFF",0.28,0.01)}
    {rays(cx,cy,660,48,"#EDFF45",0.14,0.04)}
    {nodes(cx,cy)}
    <circle cx="{cx}" cy="{cy}" r="220" fill="none" stroke="#F5F5F5" stroke-width="5"/>
    <circle cx="{cx}" cy="{cy}" r="166" fill="#0000F2" opacity="0.88"/>
    <path d="M {cx-102} {cy+58} C {cx-30} {cy+8}, {cx-58} {cy-72}, {cx} {cy-120} C {cx+58} {cy-72}, {cx+30} {cy+8}, {cx+102} {cy+58} M {cx} {cy-128} V {cy+128}" fill="none" stroke="#F5F5F5" stroke-width="13" stroke-linecap="round"/>
    <path d="M {cx-34} {cy-92} L {cx-112} {cy-146} L {cx-80} {cy-56} M {cx+34} {cy-92} L {cx+112} {cy-146} L {cx+80} {cy-56}" fill="none" stroke="#EDFF45" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="{cx}" cy="{cy-145}" r="16" fill="#EDFF45"/>'''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
 <radialGradient id="glow"><stop stop-color="#0000F2" stop-opacity=".26"/><stop offset="1" stop-color="#09091A" stop-opacity="0"/></radialGradient>
 <pattern id="grid" width="64" height="64" patternUnits="userSpaceOnUse"><path d="M64 0H0V64" fill="none" stroke="#F5F5F5" stroke-opacity=".026" stroke-width="1"/></pattern>
 <filter id="soft"><feGaussianBlur stdDeviation="28"/></filter>
</defs>
<rect width="100%" height="100%" fill="#09091A"/>
<rect width="100%" height="100%" fill="url(#grid)"/>
<circle cx="{cx}" cy="{cy}" r="1150" fill="url(#glow)" filter="url(#soft)"/>
<path d="M0 175 H3840 M0 1985 H3840" stroke="#5B6CFF" stroke-opacity=".28" stroke-width="2"/>
{graphic}
<g fill="#F5F5F5" text-anchor="{align}">
 <text x="{tx}" y="{1930 if variant==2 else 360}" font-family="DejaVu Serif,serif" font-size="{148 if variant==2 else 132}" letter-spacing="7">{title}</text>
 <text x="{tx}" y="{2025 if variant==2 else 435}" font-family="DejaVu Sans Mono,monospace" font-size="30" letter-spacing="6" fill="#EDFF45">{sub}</text>
</g>
<g font-family="DejaVu Sans Mono,monospace" font-size="22" fill="#8C8CA7" letter-spacing="4"><text x="120" y="120">NOUS RESEARCH</text><text x="3300" y="2070">OPEN SOURCE // MIT</text></g>
</svg>'''

for i in range(1,4):
    (SOURCE/f"hermes-{i}.svg").write_text(wallpaper(i))

unlock='''<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="288" viewBox="0 0 1024 288">
<g transform="translate(58 18)">
 <circle cx="126" cy="126" r="116" fill="#0000F2"/>
 <circle cx="126" cy="126" r="92" fill="none" stroke="#F5F5F5" stroke-width="4"/>
 <path d="M70 158 C110 130 94 84 126 58 C158 84 142 130 182 158 M126 54V200" fill="none" stroke="#F5F5F5" stroke-width="10" stroke-linecap="round"/>
 <path d="M104 78L66 48L82 98M148 78L186 48L170 98" fill="none" stroke="#EDFF45" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
 <circle cx="126" cy="45" r="12" fill="#EDFF45"/>
</g>
<text x="345" y="134" font-family="DejaVu Serif,serif" font-size="92" letter-spacing="8" fill="#F5F5F5">HERMES</text>
<text x="350" y="186" font-family="DejaVu Sans Mono,monospace" font-size="20" letter-spacing="6" fill="#EDFF45">NOUS RESEARCH // AGENT</text>
</svg>'''
(SOURCE/'unlock.svg').write_text(unlock)

preview='''<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">
<defs><linearGradient id="bar" x2="1"><stop stop-color="#0000F2"/><stop offset=".72" stop-color="#5B6CFF"/><stop offset="1" stop-color="#EDFF45"/></linearGradient></defs>
<image href="assets/source/hermes-1.svg" width="1920" height="1080" preserveAspectRatio="xMidYMid slice"/>
<rect x="22" y="20" width="1876" height="38" rx="10" fill="#0E0E23" fill-opacity=".96" stroke="#5B6CFF" stroke-opacity=".55"/>
<g font-family="DejaVu Sans Mono,monospace" font-size="16" fill="#F5F5F5"><text x="48" y="46">◈  HERMES</text><text x="1540" y="46">NET  ▴  82%   09:41</text><text x="916" y="46" fill="#EDFF45">1  2  3  4</text></g>
<rect x="82" y="144" width="1060" height="760" rx="18" fill="#09091A" fill-opacity=".94" stroke="url(#bar)" stroke-width="3"/>
<rect x="82" y="144" width="1060" height="46" rx="18" fill="#15152E"/><circle cx="116" cy="167" r="6" fill="#FF5C6C"/><circle cx="138" cy="167" r="6" fill="#EDFF45"/><circle cx="160" cy="167" r="6" fill="#7CF29A"/>
<g font-family="DejaVu Sans Mono,monospace" font-size="20"><text x="120" y="245" fill="#8C8CA7">cody@omarchy  ~/projects</text><text x="120" y="292" fill="#EDFF45">❯</text><text x="154" y="292" fill="#F5F5F5">hermes</text><text x="120" y="360" fill="#5DE4FF">HERMES AGENT</text><text x="120" y="401" fill="#8C8CA7">The agent that grows with you.</text><text x="120" y="478" fill="#5B6CFF">●</text><text x="154" y="478" fill="#F5F5F5">provider</text><text x="338" y="478" fill="#7CF29A">nous</text><text x="120" y="520" fill="#5B6CFF">●</text><text x="154" y="520" fill="#F5F5F5">model</text><text x="338" y="520" fill="#7CF29A">hermes-4</text><text x="120" y="602" fill="#EDFF45">›</text><text x="154" y="602" fill="#F5F5F5">How can I help?</text><rect x="120" y="642" width="900" height="96" rx="8" fill="#15152E" stroke="#33335A"/><text x="144" y="699" fill="#8C8CA7">Build something remarkable…</text></g>
<rect x="1255" y="248" width="525" height="430" rx="18" fill="#0E0E23" fill-opacity=".96" stroke="#5B6CFF" stroke-width="2"/>
<text x="1300" y="306" font-family="DejaVu Sans Mono,monospace" font-size="16" fill="#EDFF45" letter-spacing="3">// SYSTEM</text><text x="1300" y="372" font-family="DejaVu Serif,serif" font-size="42" fill="#F5F5F5">Everything to</text><text x="1300" y="422" font-family="DejaVu Serif,serif" font-size="42" fill="#F5F5F5">Power Hermes</text><g font-family="DejaVu Sans Mono,monospace" font-size="16" fill="#8C8CA7"><text x="1300" y="492">MEMORY       ONLINE</text><text x="1300" y="532">GATEWAY      ACTIVE</text><text x="1300" y="572">SUBAGENTS    READY</text></g><rect x="1300" y="612" width="220" height="4" fill="#EDFF45"/>
</svg>'''
(ROOT/'preview.svg').write_text(preview)
print('generated', *(str(p) for p in sorted(SOURCE.glob('*.svg'))), ROOT/'preview.svg')
