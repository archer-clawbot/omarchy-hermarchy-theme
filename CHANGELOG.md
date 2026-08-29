# Changelog

## v1.0.0

Hermarchy's first public-distribution release.

### Base theme

- Restrained near-black, graphite, warm-white, and semantic-cyan visual system.
- Omarchy v4 `colors.toml` and native `shell.toml` contracts.
- Coordinated shell, launcher, terminal/editor, Chromium, notifications,
  Hyprlock, btop, icons, and legacy Waybar styling.
- Three original 3840×2400 wallpapers and a transparent lock mark.
- Real desktop preview and gallery-ready WebP.
- Documented install, update, wallpaper, switch-away, and removal flows.

### Optional agent integration

- Explicitly opt-in user-local Quickshell bar widget and click panel.
- Provider-neutral validated agent-state contract and read-only Hermes adapter.
- Muted idle/unavailable/unknown, semantic executing/waiting/completed/failed
  states, and bounded contract-backed details.
- Deterministic install, reinstall, update, disable, recovery, and removal
  instructions without package-owned file changes.

### Distribution readiness

- First-run documentation reorganized for new users.
- Tested-environment and compatibility boundaries documented.
- Public-safety audit for personal paths, machine labels, credentials, and
  development assumptions.
- Current public-safe screenshots for base and optional surfaces.
- Repository link, asset, mode, Python, QML, and plugin validation gates.

### Known limitations

- Base theme support is verified on Omarchy `4.0.1-1`; older Omarchy releases
  are not claimed.
- The optional plugin requires the Omarchy v4 Quickshell plugin API on Linux.
- Hermes is not installed or configured by Hermarchy.
- Waybar support is a manual legacy helper rather than a native Omarchy v4
  integration.
- Terminal completed/failed states are intentionally temporary.
