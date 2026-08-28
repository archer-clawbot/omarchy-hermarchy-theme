#!/usr/bin/env bash
set -euo pipefail

if systemctl --user is-active --quiet hermes-gateway.service 2>/dev/null; then
  printf '%s\n' '{"text":"HERMES ● ONLINE","class":"online","tooltip":"Hermes Gateway // active"}'
else
  printf '%s\n' '{"text":"HERMES ○ OFFLINE","class":"offline","tooltip":"Hermes Gateway // inactive"}'
fi
