#!/bin/sh
###############################################################################
# register-connectors.sh – авторегистрация всех *.json из /connectors
# выводит максимум полезной отладочной информации
###############################################################################
set -euo pipefail

cyan()  { printf '\033[36m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
red()   { printf '\033[31m%s\033[0m\n' "$*"; }
bold()  { printf '\033[1m%s\033[0m\n' "$*"; }

bold '▶ Registering connectors'
cd /connectors || exit 0

set -- *.json
if [ "$1" = '*.json' ]; then
  red '⚠  no json found – nothing to register'
  exit 0
fi

total=$#
cyan "Found $total connector definition(s): $*"
echo

# таблица итогов
RESULTS=""

for f in "$@"; do
  name="${f%.json}"
  cyan "• $name"

  # ===== DELETE (игнорируем 404) ==========================================
  del_code=$(curl -s -o /dev/null -w "%{http_code}" \
                  -X DELETE "http://kafka-connect:8083/connectors/$name")
  [ "$del_code" = 404 ] && del_msg='(not present)' || del_msg="($del_code)"
  printf '  ⟲ DELETE %s\n' "$del_msg"

  # ===== POST =============================================================
  response=$(mktemp)
  post_code=$(curl -s -o "$response" -w "%{http_code}" \
                   -X POST -H 'Content-Type: application/json' \
                   --data "@$f" \
                   "http://kafka-connect:8083/connectors")

  if [ "$post_code" = 201 ]; then
    green "  ✓ created   → HTTP $post_code"
    RESULTS="$RESULTS\n$name\tSUCCESS"
  else
    red   "  ✗ failed    → HTTP $post_code"
    printf '    ↳ %s\n' "$(cat "$response" | tr -d '\n' | cut -c1-120)…"
    RESULTS="$RESULTS\n$name\tFAIL($post_code)"
  fi
  rm -f "$response"
  echo
done

bold '✔ Summary'
printf '%b\n' "$RESULTS" | column -t -s $'\t'
