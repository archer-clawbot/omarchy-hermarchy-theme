# Hermes // Nous for Omarchy

![Hermes // Nous desktop](preview.png)

A precision command environment for [Omarchy](https://omarchy.org/), inspired
by [Hermes Agent](https://hermes-agent.nousresearch.com/) and
[Nous Research](https://nousresearch.com/).

This is not a dark theme with a branded wallpaper. It treats Omarchy as the
native operating environment for Hermes: human content is warm white, system
structure is graphite, and cyan appears only when the agent or machine is
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
https://github.com/archer-clawbot/omarchy-hermes-theme.git
```

### Terminal

```sh
omarchy theme install https://github.com/archer-clawbot/omarchy-hermes-theme.git
omarchy theme set hermes
```

The repository remains `omarchy-hermes-theme` so Omarchy derives the stable
theme slug `hermes`. Its display identity is **Hermes // Nous**.

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
| Agent | Hermes signal | `#61D6FF` |
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
- A transparent Hermes lock-screen mark
- A real 1920×1080 Omarchy desktop preview
- A gallery-ready 1200×675 WebP
- Reproducible SVG/PNG artwork generator
- Optional gateway-status module for Waybar users
- Optional Hermes Fastfetch experience

## Native Hermes integration

Modern Omarchy exposes Hermes through its native Agents panel when the
Omarchy–Hermes integration is installed. This theme styles that surface without
patching package-managed files.

The optional status integrations are intentionally opt-in:

### Fastfetch

```sh
./extras/fastfetch/hermes-fastfetch.sh
```

It presents the node, local Hermes Gateway state, and a restrained system
summary using the theme's semantic colors.

### Waybar

Current Omarchy uses Quickshell rather than Waybar. Older installations and
Waybar users can add the JSON status module documented in:

```text
extras/waybar/README.md
```

It reports `HERMES ● ONLINE` only when the local gateway service is active.
It never starts or modifies the service.

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
assets/themes/hermes.webp
```

Then add the alphabetized theme entry linking to this repository. The preview
is a real Omarchy desktop capture, not a mockup.

## Rights

All bundled artwork is original and generated from source under
`assets/source/`. No imagery from the Hermes or Nous websites is redistributed.
Hermes, Nous Research, and their marks belong to their respective owners. This
is an unofficial community theme and does not imply sponsorship or endorsement.
See `NOTICE`.

## License

Theme code and original artwork are released under the MIT License.
