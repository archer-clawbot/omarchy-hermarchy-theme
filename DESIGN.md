# Hermarchy Design System

## Premise

Omarchy is the shell. Hermarchy is the independent visual system.

The environment should resemble a UNIX research workstation or mission-control
instrument: legible, restrained, stateful, and almost entirely opaque. It must
not resemble cyberpunk, Matrix green, a neon dashboard, or a generic purple AI
product.

## Semantic layers

### Human

Warm white (`#F1F1EC`) carries prose, commands, source code, and other content
that belongs to the user. Secondary human content uses `#9B9E9F`.

### System

Near-black and graphite carry structure: backgrounds, surfaces, dividers,
metadata, and inactive controls. Borders are hairlines, not glowing frames.

### Agent

Cyan (`#61D6FF`) marks active intelligence: the cursor, current agent
state, focused launcher result, live telemetry, or an executing operation.
Bright cyan (`#8DE4FF`) is reserved for immediate focus.

State colors remain muted and literal:

- success `#86D993`
- warning `#E2C275`
- error `#E46E6E`

## Typography

Use IBM Plex Sans or Inter for interface text and IBM Plex Mono or JetBrains
Mono for code, telemetry, and metadata. Uppercase belongs to compact labels and
system identifiers, not ordinary prose.

Recommended hierarchy:

```text
HERMARCHY             theme identity
Agent environment     human-readable surface title
MODEL / STATUS        metadata label
Gateway active        human-readable state
```

## Geometry

- square or nearly square surfaces
- 1 px graphite borders
- sparse technical rules
- no decorative glass
- no heavy blur
- near-opaque terminal and launcher surfaces
- short, quiet compositor transitions

The stock Omarchy theme contract controls colors and shell surfaces, not
compositor animation behavior. This repository does not overwrite user-owned
Hyprland behavior.

## Wallpaper system

1. **Hermarchy Command** — flagship boot/command environment with a low-opacity
   radial routing field.
2. **Hermarchy Node** — asymmetric local-agent routing map with negative space.
3. **Capabilities** — numbered Connect, Remember, Schedule, Delegate system
   blocks.

All wallpapers are original SVG compositions generated at 3840×2400. They are
designed for 16:10 desktops and retain their primary content in a 16:9 gallery
crop.

## Application behavior

- Terminal and editor syntax use muted semantic distinctions, not a rainbow.
- Launcher selections use a dark raised surface and one cyan state line.
- Notifications are opaque graphite event cards.
- btop uses gray capacity and cyan utilization; warning and error colors appear
  only at real thresholds.
- Lock surfaces remain near-black and reveal cyan only during authentication.
- Chromium uses the system background; it does not become a bright brand panel.

## Integration boundary

A public Omarchy theme must remain safe and portable. It does not:

- edit `/usr/share/omarchy` or `/usr/bin`;
- replace package-owned Quickshell components;
- rewrite a user's prompt or browser homepage;
- start agent services;
- install custom fonts or icons;
- change compositor behavior.

Optional status scripts are inspectable, user-owned, and read-only. This keeps
the gallery theme installable while leaving room for deeper agent integration
on systems that explicitly opt in.
