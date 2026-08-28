#!/usr/bin/env bash
set -euo pipefail

if systemctl --user is-active --quiet hermes-gateway.service 2>/dev/null; then
  printf '%s\n' '{"text":"AGENT ● ONLINE","class":"online","tooltip":"Local agent gateway // active"}'
else
  printf '%s\n' '{"text":"AGENT ○ OFFLINE","class":"offline","tooltip":"Local agent gateway // inactive"}'
fi
