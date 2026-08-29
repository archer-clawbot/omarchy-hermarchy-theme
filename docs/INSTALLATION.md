# Installation, update, and removal

This guide covers the supported public flow on Omarchy v4. The base theme and
the optional Hermes-aware integration are separate installations.

## Base theme: first install

### Omarchy menu

1. Open the Omarchy menu with `Super + Space`.
2. Choose **Install > Style > Theme**.
3. Paste:

   ```text
   https://github.com/archer-clawbot/omarchy-hermarchy-theme.git
   ```

Omarchy clones the repository, derives the slug `hermarchy`, filters executable
theme inputs, stages the passive assets, and activates the theme.

### Terminal

```sh
omarchy theme install https://github.com/archer-clawbot/omarchy-hermarchy-theme.git
omarchy theme set hermarchy
```

Verify the result:

```sh
omarchy theme current
omarchy theme dir hermarchy
omarchy theme bg current
```

The first command should report `Hermarchy`. The installed clone is normally at
`~/.config/omarchy/themes/hermarchy`.

Cycle the three supplied backgrounds:

```sh
omarchy theme bg next
```

The base install does not create a plugin under `~/.config/omarchy/plugins` and
does not install `~/.local/bin/hermarchy-agent-state`.

## Optional agent-aware integration

Prerequisites are listed in [COMPATIBILITY.md](COMPATIBILITY.md). Hermes itself
is optional: without it, the surface installs but reports unavailable/muted.

Install and enable:

```sh
theme_dir="$(omarchy theme dir hermarchy)"
"$theme_dir/extras/quickshell/install.sh"
```

Install without changing the active bar:

```sh
"$theme_dir/extras/quickshell/install.sh" --no-enable
```

Enable a previously copied plugin:

```sh
omarchy-shell shell rescanPlugins
omarchy plugin enable io.github.archer-clawbot.hermarchy-agent --before omarchy.agents
```

Verify discovery and payload validation:

```sh
omarchy plugin list --json
omarchy plugin validate \
  "$HOME/.config/omarchy/plugins/io.github.archer-clawbot.hermarchy-agent"
"$HOME/.local/bin/hermarchy-agent-state" collect
```

Expected user-local destinations:

```text
~/.local/bin/hermarchy-agent-state
~/.config/omarchy/plugins/io.github.archer-clawbot.hermarchy-agent/
```

The installer does not write package-owned Omarchy, Quickshell, Hyprland, or
Hermes files.

## Update

Update the git-managed theme clone and reapply its passive assets:

```sh
omarchy theme update
omarchy theme set hermarchy
```

The optional integration is copied rather than git-managed. Refresh it from the
updated theme clone:

```sh
theme_dir="$(omarchy theme dir hermarchy)"
"$theme_dir/extras/quickshell/install.sh"
```

The optional installer supports both an upgrade from an earlier Hermarchy
revision and a reinstall over already-correct files. It validates the complete
replacement before enabling it.

## Disable without removing

Keep the optional integration installed but remove it from the active bar:

```sh
omarchy plugin disable io.github.archer-clawbot.hermarchy-agent
```

Enable it again with:

```sh
omarchy plugin enable io.github.archer-clawbot.hermarchy-agent --before omarchy.agents
```

## Remove the optional integration

Disable and remove the plugin through Omarchy, then remove the shared adapter
only if no other local workflow uses it:

```sh
omarchy plugin disable io.github.archer-clawbot.hermarchy-agent
omarchy plugin remove io.github.archer-clawbot.hermarchy-agent --yes
rm -- "$HOME/.local/bin/hermarchy-agent-state"
```

For a non-git user-local plugin, Omarchy moves the removed directory to an inert
backup and prints its exact path. Keep it for rollback or delete that exact path
manually after inspection. The active plugin path is gone either way.

## Remove the base theme

Never delete the active theme first. Switch to another installed theme, verify
the change, then remove Hermarchy:

```sh
omarchy theme set tokyo-night
omarchy theme current
omarchy theme remove hermarchy
```

Choose any installed theme in place of `tokyo-night`. Removal deletes only
`~/.config/omarchy/themes/hermarchy`; the currently staged replacement theme
continues normally.

## Recover a partial optional installation

The supported recovery is to rerun the same installer from the installed theme
clone:

```sh
theme_dir="$(omarchy theme dir hermarchy)"
"$theme_dir/extras/quickshell/install.sh"
```

This covers:

- adapter present but plugin absent;
- plugin present but adapter absent;
- an older complete payload;
- already-correct files;
- copied files that were never enabled.

If copying succeeds but activation is unavailable because the shell was not
running, rescan and enable after the shell starts:

```sh
omarchy-shell shell rescanPlugins
omarchy plugin enable io.github.archer-clawbot.hermarchy-agent --before omarchy.agents
```

Do not copy individual QML files into package directories. If the explicit
installer reports a validation or path error, leave the reported prior payload
in place and resolve that concrete error before retrying.

## Restore normal Omarchy behavior

A complete rollback is:

1. disable/remove the optional plugin;
2. remove the adapter if unused elsewhere;
3. switch to another installed theme;
4. remove the Hermarchy theme clone.

No step modifies `/usr/share/omarchy`, `/usr/bin`, package-owned Quickshell, or
global Hyprland configuration.
