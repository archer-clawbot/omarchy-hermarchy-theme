#!/usr/bin/env bash
set -euo pipefail

cyan=$'\033[38;2;97;214;255m'
white=$'\033[38;2;241;241;236m'
muted=$'\033[38;2;96;100;104m'
reset=$'\033[0m'

if systemctl --user is-active --quiet hermes-gateway.service 2>/dev/null; then
  gateway="${cyan}ONLINE${reset}"
else
  gateway="${muted}OFFLINE${reset}"
fi

printf '\n%s          /\\-_=+|< -/= ~:*-/\n\n%s          H E R M A R C H Y%s\n\n' "$cyan" "$white" "$reset"
printf '%sTHEME     %sHermarchy%s\n' "$muted" "$white" "$reset"
printf '%sGATEWAY   %b\n' "$muted" "$gateway"
printf '%sNODE      %sOMARCHY-01%s\n\n' "$muted" "$white" "$reset"
printf '%s────────────────────────────────────────%s\n\n' "$muted" "$reset"

fastfetch \
  --logo none \
  --color-keys 6 \
  --color-title 7 \
  --structure OS:Kernel:WM:Terminal:CPU:GPU:Memory
