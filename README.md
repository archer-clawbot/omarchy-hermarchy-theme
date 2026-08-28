# Hermes for Omarchy

![Hermes Omarchy theme preview](preview.png)

An electric-blue Omarchy theme inspired by the visual language of
[Hermes Agent](https://hermes-agent.nousresearch.com/) and
[Nous Research](https://nousresearch.com/): electric Hermes blue, paper white,
and the signature acid-yellow accent.

The theme pairs editorial serif display moments with a precise terminal
palette, technical framing, and a 1704 Hermes engraving treated in the
Portal's monochrome print language. It remains quiet behind windows while
making focus, selection, and agent status obvious.

## Install

### Omarchy menu

1. Open the Omarchy menu with `Super + Space`.
2. Choose **Install > Style > Theme**.
3. Paste:

   ```text
   https://github.com/archer-clawbot/omarchy-hermes-theme.git
   ```

### Terminal

```sh
omarchy theme install https://github.com/archer-clawbot/omarchy-hermes-theme.git
```

The legacy command remains supported by Omarchy releases that provide it:

```sh
omarchy-theme-install https://github.com/archer-clawbot/omarchy-hermes-theme.git
```

After installation, choose **Hermes** in the theme switcher or run:

```sh
omarchy theme set hermes
```

Cycle the three included 4K backgrounds with:

```sh
omarchy theme bg next
```

## Palette

| Role | Color |
|---|---|
| Hermes primary | `#0000F2` |
| Deep blue surface | `#00008E` |
| Elevated blue | `#0000C0` |
| Acid accent | `#EDFF45` |
| Paper foreground | `#F5F5F5` |
| Cyan | `#70E7FF` |
| Success | `#89F7A1` |
| Error | `#FF6B7A` |

The exact website blue dominates the wallpaper and shell chrome. Deeper blue
surfaces preserve terminal legibility, while paper white and acid yellow carry
the site's hard-edged editorial contrast.

## Included

- Omarchy `colors.toml` and current `shell.toml` surfaces
- Omarchy-generated terminal, editor, browser, and TUI palettes
- Hyprlock, Walker, Waybar, Mako, Chromium, icons, and btop accents
- One Portal-inspired 3840×2400 engraving wallpaper and two 3840×2160
  geometric alternatives
- A transparent Hermes unlock mark (`unlock.png`)
- A 1920×1080 repository preview
- A gallery-ready 1200×675 WebP (`gallery-preview.webp`)
- Reproducible SVG sources and asset build script

## Rebuild artwork

The checked-in PNG and WebP files are ready to use. To reproduce them, install
`librsvg` and ImageMagick, then run:

```sh
python scripts/build_assets.py
for source in assets/source/hermes-{2,3}.svg; do
  name="$(basename "${source%.svg}")"
  rsvg-convert -w 3840 -h 2160 "$source" -o "backgrounds/$name.png"
done
python scripts/build_portal_wallpaper.py
rsvg-convert -w 1024 -h 288 assets/source/unlock.svg -o unlock.png
magick preview.png -strip -resize '1200>' -quality 80 gallery-preview.webp
```

## Gallery submission asset

Omarchy's theme gallery expects a 16:9 screenshot converted with:

```sh
magick preview.png -strip -resize '1200>' -quality 80 hermes.webp
```

`gallery-preview.webp` is already produced to that contract. In an
`omacom-io/omarchy-site` pull request, add it as
`assets/themes/hermes.webp` and add the alphabetized figure entry linking to
this repository.

## Design and rights

No imagery from the Nous Portal or Hermes websites is redistributed. The main
wallpaper uses a licensed historical engraving from the Wellcome Collection,
modified into a cobalt-and-paper duotone; complete source and attribution are
in `NOTICE`. The remaining artwork is original. Hermes, Nous Research, and
their marks belong to Nous Research. This is an unofficial community theme and
is not an endorsement by or official release of Nous Research.

## License

Theme code and original artwork are released under the MIT License. See
`LICENSE`.
