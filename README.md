# Hermarchy for Omarchy

![Hermarchy desktop](preview.png)

A precision agent command environment for [Omarchy](https://omarchy.org/).
Hermarchy is an independent community theme: human content is warm white,
system structure is graphite, and cyan appears only when an agent or machine is
active.

```text
HUMAN LAYER   warm white   documents, text, primary UI
SYSTEM LAYER  graphite     borders, metadata, inactive state
AGENT LAYER   cyan         execution, focus, agent status
```

## Install

### Omarchy menu

Open `Super + Space`, choose **Install > Style > Theme**, and paste:

```text
https://github.com/archer-clawbot/omarchy-hermarchy-theme.git
```

### Terminal

```sh
omarchy theme install https://github.com/archer-clawbot/omarchy-hermarchy-theme.git
omarchy theme set hermarchy
```

The repository name gives the theme its stable slug and display identity:
**Hermarchy**.

Cycle the three included backgrounds with:

```sh
omarchy theme bg next
```

## Visual system

| Layer | Role | Color |
|---|---|---|
| Human | Primary text | `#F1F1EC` |
| Human | Secondary text | `#9B9E9F` |
| System | Background | `#08090A` |
| System | Surface | `#101214` |
| System | Raised surface | `#16191C` |
| System | Border | `#272B2F` |
| System | Muted metadata | `#606468` |
| Agent | Signal | `#61D6FF` |
| Agent | Active signal | `#8DE4FF` |
| State | Success | `#86D993` |
| State | Warning | `#E2C275` |
| State | Error | `#E46E6E` |

The governing rule is **95% monochrome, 5% signal color**. Cyan is semantic,
not decorative.

## Included

- Current Omarchy `colors.toml` semantic contract
- Native Omarchy/Quickshell surfaces through `shell.toml`
- Generated terminal, Neovim, GTK, editor, and TUI palettes
- Walker, Waybar, Mako, Hyprlock, Chromium, icons, and btop accents
- Three original 3840×2400 command-environment wallpapers
- A transparent Hermarchy lock-screen mark
- A real 1920×1080 Omarchy desktop preview
- A gallery-ready 1200×675 WebP
- Reproducible SVG/PNG artwork generator
- Optional read-only agent-status helpers

## Optional agent integration

Modern Omarchy exposes installed agents through its native Agents panel. This
theme styles that surface without patching package-managed files.

The optional status integrations are intentionally opt-in:

### Fastfetch

```sh
./extras/fastfetch/hermarchy-fastfetch.sh
```

It presents the node, local agent gateway state, and a restrained system summary
using the theme's semantic colors. The node defaults to the machine hostname;
set `HERMARCHY_NODE_NAME` to provide a deliberate display name such as
`RIPPER`, `ORNITH`, or `LAB-01`.

### Waybar

Current Omarchy uses Quickshell rather than Waybar. Older installations and
Waybar users can add the JSON status module documented in
`extras/waybar/README.md`. It reports agent availability and never starts or
modifies a service.

## Design boundaries

A theme repository can coordinate color, surfaces, wallpaper, lock screen,
terminal, editor, browser, launcher, notifications, and TUI applications. It
cannot safely replace Omarchy's package-owned Quickshell layout, rewrite the
user's shell prompt, or add compositor behavior. Those changes are excluded by
design rather than hidden in an installer.

The active border is therefore a precise neutral hairline. Cyan focus appears
inside controls and agent state surfaces; no global compositor files are
mutated.

See [DESIGN.md](DESIGN.md) for the complete visual and semantic rationale.

## Rebuild artwork

The checked-in PNG/WebP files are ready to use. To rebuild the original
wallpapers and lock asset, install `librsvg`, then run:

```sh
python scripts/build_assets.py
```

A gallery screenshot must be captured from a real themed desktop. It is not
synthesized by the artwork script. Convert the approved screenshot with:

```sh
magick preview.png -strip -resize '1200>' -quality 80 gallery-preview.webp
```

## Gallery submission

For `omacom/omarchy-site`, add `gallery-preview.webp` as:

```text
assets/themes/hermarchy.webp
```

Then add the alphabetized theme entry linking to this repository. The preview
is a real Omarchy desktop capture, not a mockup.

## Rights

All bundled artwork is original and generated from source under
`assets/source/`. Hermarchy is an independent community theme and does not use
third-party names, logos, or artwork as its identity. See `NOTICE`.

## License

Theme code and original artwork are released under the MIT License.
