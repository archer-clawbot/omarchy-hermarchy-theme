# Hermarchy Quickshell Agent Surface

This optional user-local Omarchy plugin is the first visual consumer of
`agent-state.schema.json`. It keeps the persistent bar signal deliberately
small and opens a richer numbered panel on click.

```text
idle         HERMES ·          muted
executing    HERMES ●          cyan
waiting      HERMES ● INPUT    amber
completed    HERMES ● DONE     green (collector retains it for five minutes)
failed       HERMES ● FAILED   red (collector retains it for five minutes)
unavailable  HERMES ·          muted
unknown      HERMES ·          muted
```

The panel shows only contract-backed fields: task, model, active workers, node,
gateway, and last event. It does not display token, context, memory, or
utilization guesses.

## Architecture

```text
Hermes structured local state
  -> hermarchy-agent-state adapter
  -> agent-state.schema.json validator
  -> hermarchy-state-read
  -> StateModel.js fail-muted projection
  -> native Omarchy bar widget and click panel
```

The Linux reader acts as a child subreaper, captures at most 64 KiB, gives
collection a five-second deadline and validation a one-second deadline, and
enforces both with a one-second hard-kill grace. It kills and reaps the complete
descendant tree—including children that create a new session—before validating
and emitting those exact bytes. If Linux process-tree inspection is unavailable,
the reader kills the known process group as a best effort and fails closed rather
than treating the tree as empty.
Invalid output, oversized output, a timeout, or a failed refresh becomes
`unknown`/muted. `StateModel.js` independently checks the complete record
shape, enums, timestamps, field types, and terminal-state invariants before
using it.
The plugin never writes runtime state and does not patch package-owned Omarchy,
Quickshell, or Hyprland files.

## Install

From the theme repository:

```sh
./extras/quickshell/install.sh
```

That explicit opt-in action:

1. rejects symlinked `$HOME` ancestors, destination components, and existing
   plugin-tree entries, and requires Omarchy validation;
2. builds the exact plugin payload in a private temporary staging directory and
   validates it before writing either destination;
3. anchors the real `$HOME` directory and creates every destination through
   no-follow directory descriptors, so a path replaced after prevalidation is
   never traversed;
4. transactionally swaps the adapter at `~/.local/bin/hermarchy-agent-state`
   and the plugin at
   `~/.config/omarchy/plugins/io.github.archer-clawbot.hermarchy-agent`;
5. holds the installed adapter and plugin descriptors, requires exact staged
   bytes and file names, validates a private snapshot of the installed plugin
   bytes, then reopens every destination ancestor from the anchored `$HOME` and
   compares ancestor and artifact identities plus final bytes; it also rechecks
   the absolute `$HOME` identity and restores both complete prior artifacts on
   any swap, read-back, identity, mutation, or validation failure;
6. explicitly rescans discovery and enables the plugin immediately before the
   native Agents widget unless `--no-enable` was requested.

To copy and validate without changing the active bar layout:

```sh
./extras/quickshell/install.sh --no-enable
```

Then enable it later:

```sh
omarchy plugin enable io.github.archer-clawbot.hermarchy-agent --before omarchy.agents
```

Middle-click the bar signal to refresh immediately. The normal polling interval
is two seconds and can be adjusted through Omarchy's bar widget settings.

## Remove

```sh
omarchy plugin remove io.github.archer-clawbot.hermarchy-agent --yes
```

The adapter is shared with the command-line contract workflow and is therefore
not removed automatically. Remove it separately only when nothing else uses it:

```sh
rm "$HOME/.local/bin/hermarchy-agent-state"
```

## Tests

```sh
python3 -m unittest tests.test_agent_state tests.test_quickshell_plugin -v
QT_QPA_PLATFORM=offscreen /usr/lib/qt6/bin/qmltestrunner \
  -input tests/quickshell -import /usr/share/omarchy/shell
```
