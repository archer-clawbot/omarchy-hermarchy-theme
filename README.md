# Hermes for Omarchy

![Hermes Omarchy theme preview](preview.png)

An electric-blue Omarchy theme inspired by the visual language of
[Hermes Agent](https://hermes-agent.nousresearch.com/) and
[Nous Research](https://nousresearch.com/): deep portal navy, Hermes blue,
paper white, and the signature acid-yellow accent.

The theme pairs editorial serif display moments with a precise terminal
palette and original network/radiant-line artwork. It is designed to remain
quiet behind windows while making focus, selection, and agent status obvious.

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
| Portal background | `#09091A` |
| Elevated surface | `#15152E` |
| Hermes blue | `#0000F2` |
| Readable blue | `#5B6CFF` |
| Acid accent | `#EDFF45` |
| Paper foreground | `#F5F5F5` |
| Cyan | `#5DE4FF` |
| Success | `#7CF29A` |
| Error | `#FF5C6C` |

The exact brand blue is retained for identity and gradients. The lighter blue
is used when text or thin UI chrome needs more contrast against the dark
background.

## Included

- Omarchy `colors.toml` and current `shell.toml` surfaces
- Omarchy-generated terminal, editor, browser, and TUI palettes
- Hyprlock, Walker, Waybar, Mako, Chromium, icons, and btop accents
- Three original 3840×2160 wallpapers
- A transparent Hermes unlock mark (`unlock.png`)
- A 1920×1080 repository preview
- A gallery-ready 1200×675 WebP (`gallery-preview.webp`)
- Reproducible SVG sources and asset build script

## Rebuild artwork

The checked-in PNG and WebP files are ready to use. To reproduce them, install
`librsvg` and ImageMagick, then run:

```sh
python scripts/build_assets.py
for source in assets/source/hermes-*.svg; do
  name="$(basename "${source%.svg}")"
  rsvg-convert -w 3840 -h 2160 "$source" -o "backgrounds/$name.png"
done
rsvg-convert -w 1920 -h 1080 preview.svg -o preview.png
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

All wallpaper and preview artwork in this repository is original and generated
from the SVG sources under `assets/source/`; no website imagery is bundled.
Hermes, Nous Research, and their marks belong to Nous Research. This is an
unofficial community theme and is not an endorsement by or official release
of Nous Research. See `NOTICE`.

## License

Theme code and original artwork are released under the MIT License. See
`LICENSE`.
