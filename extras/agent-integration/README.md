# Hermarchy Agent Integration

This directory is the optional Tier 2 integration. It is not executed or
installed by the Omarchy theme installer and it never modifies package-owned
Quickshell, Hyprland, or Omarchy files.

## State contract

`agent-state.schema.json` defines a provider-neutral versioned record. The first
adapter, `hermarchy-agent-state`, reads only local structured sources:

- the Hermes state database, opened with SQLite URI `mode=ro`; text and timestamp
  values are bounded or type-guarded at SQL projection using maximum-plus-one
  sentinels and original SQLite storage metadata; SQL NULL values remain null;
- unfinished local delegation records, validated and counted with bounded scalar
  queries;
- the user-level gateway service state;
- an optional short-lived runtime snapshot.

It does not call remote nodes, scrape terminal output, or invent context-window,
memory, tool, skill, or utilization values.

| State | Signal | Meaning |
|---|---|---|
| `idle` | `muted` | Installed and observable, with no fresh execution |
| `executing` | `cyan` | Fresh open-session activity or an unfinished worker |
| `waiting` | `amber` | Explicit fresh runtime request for human input |
| `completed` | `green` | Explicit success reason retained for 300 seconds |
| `failed` | `red` | Explicit failure/error/exception retained for 300 seconds |
| `unavailable` | `muted` | Agent executable is unavailable |
| `unknown` | `muted` | Structured state could not be read |

Cyan is semantic, not decorative. The validator rejects a state paired with the
wrong signal. Any recognized unfinished worker has global `executing`/cyan
precedence; neither a runtime snapshot nor an unavailable executable probe can
hide delegated work that is still active.

If any database schema, storage type, session field, timestamp chronology, or
delegation state fails validation, all database-derived fields are discarded
before another source is considered.

## Collect and validate

```sh
./extras/agent-integration/hermarchy-agent-state collect |
  ./extras/agent-integration/hermarchy-agent-state validate -
```

Validation reads at most 64 KiB from stdin or a nonblocking, no-follow regular
file. Oversized, special-file, invalid UTF-8, malformed, or excessively nested
inputs are rejected with a controlled error. RFC 3339 timestamps are checked
against both the exact grammar and calendar/timezone component bounds; permissive
`24:00:00` or `+00:60` forms are rejected.

The collector defaults to:

- database: `${HERMES_HOME:-$HOME/.hermes}/state.db`;
- node: `hostname`;
- execution freshness: 300 seconds;
- terminal-state retention: 300 seconds;
- runtime snapshot: `~/.local/state/hermarchy/runtime.json`;
- runtime snapshot maximum age: 60 seconds;
- gateway: bounded local `systemctl --user is-active` observation.

A non-default profile should pass its database explicitly:

```sh
hermarchy-agent-state collect --db "$HERMES_HOME/state.db"
```

## Explicit runtime snapshots

`waiting` is never inferred from an old open session. A runtime that knows it is
waiting for a person may atomically publish:

```json
{
  "state": "waiting",
  "updatedAt": 2000000000,
  "task": "Approve package update",
  "detail": "Human input required"
}
```

Write to a sibling temporary file, then rename it to `runtime.json`. Snapshots
older than 60 seconds, timestamped in the future, larger than 16 KiB, malformed,
containing unexpected fields, using an unknown state, or carrying a task over
512 characters or detail over 2048 characters are ignored. A `completed` or
`failed` snapshot must also include `endReason` from the collector's corresponding
explicit success or failure allowlist; terminal state alone cannot produce green
or red. Non-terminal snapshots must omit `endReason`. This prevents a crashed or
malformed producer from leaving the desktop permanently cyan, amber, red, or
green.

Runtime input is opened nonblocking with symlink following disabled and accepted
only when the opened descriptor is a regular file; FIFOs and other special files
are ignored.

## Optional user-local install

```sh
install -Dm755 extras/agent-integration/hermarchy-agent-state \
  "$HOME/.local/bin/hermarchy-agent-state"
mkdir -p "$HOME/.local/state/hermarchy"
```

No timer or UI mutation is installed by this adapter-only command. The first
consumer now lives in `../quickshell/`: a user-local Omarchy plugin that invokes
the collector, validates the exact output, and renders the semantic signal
without patching `/usr/share/omarchy/shell`.

## Tests

```sh
python3 -m unittest tests.test_agent_state -v
```
