# Compatibility and tested environment

Compatibility claims are intentionally limited to environments exercised for
the v1.0.0 distribution gate.

## Verified environment

| Component | Verified version/status |
|---|---|
| Omarchy | `4.0.1-1` |
| Quickshell | `0.3.1-1` |
| Qt Declarative | `6.11.2-1` |
| Hyprland | `0.56.2` |
| Python | `3.14.7` |
| Git | `2.55.0` |
| Bash | `5.3.15` |
| systemd | `261` |
| Architecture | Arch Linux, x86_64, user-level Omarchy session |

The base theme was installed, activated, cycled, updated, switched away from,
and removed through the real Omarchy v4 commands in an isolated user-local
home. The optional plugin was validated with Omarchy's real manifest validator
and exercised through the current user-local plugin API.

## Base theme requirements

Required:

- Omarchy v4;
- `git` (used by `omarchy theme install` and `omarchy theme update`).

The installed repository provides passive theme assets. Omarchy generates and
applies terminal/editor/application files from `colors.toml` and applies native
shell colors from `shell.toml`. No Hermes or Quickshell plugin is required for
the base theme.

No compatibility claim is made for Omarchy v3 or non-Omarchy distributions.

## Optional Quickshell integration requirements

Required:

- Linux;
- Omarchy's current user-local plugin commands;
- Quickshell with the Omarchy v4 shell plugin API;
- `python3`;
- `omarchy` and `omarchy-shell`.

The reader relies on Linux `/proc` process metadata to enforce its bounded child
lifetime. If state collection, validation, or process inspection cannot be
trusted, the UI fails muted.

Optional:

- Hermes Agent. If absent, the adapter emits `unavailable`/muted.
- `systemctl --user`. When available, it reports local Hermes gateway state;
  failure does not start or change the service.
- A Hermes state database under `${HERMES_HOME:-$HOME/.hermes}/state.db`.
  Missing state produces a neutral result rather than fabricated telemetry.

The integration does not require a network connection at runtime and does not
query remote nodes.

## Waybar status

Current Omarchy v4 uses Quickshell. `extras/waybar/hermarchy-status.sh` is a
manual helper for Waybar users and older/custom environments; it is not
installed, enabled, or configured automatically. Its JSON output and shell
syntax were checked on the verified host, but no Waybar release is claimed as a
supported native Omarchy v4 surface.

## Optional development tools

These are needed only for rebuilding or validating repository assets:

- ImageMagick `7.1.2-30` for preview conversion and image checks;
- librsvg `2.62.3-1` for rebuilding SVG wallpaper/lock sources;
- Qt's `qmltestrunner` and `qmllint` for QML tests.

Checked-in PNG/WebP assets are ready to use; normal installation does not need
ImageMagick or librsvg.

## Known limitations

- The optional agent UI is a Linux/Omarchy v4 integration, not a portable
  desktop widget for other shells.
- Completed and failed states are temporary and retained by the collector for
  five minutes.
- Waiting state appears only when a fresh explicit local runtime snapshot asks
  for human input.
- The Waybar helper reports only local gateway availability and is not equivalent
  to the Quickshell state panel.
- Firefox-family browser theming follows Omarchy's own capabilities; Hermarchy
  does not patch browsers independently.
