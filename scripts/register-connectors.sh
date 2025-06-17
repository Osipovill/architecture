#!/bin/sh
set -eu

echo '▶ Registering connectors'
cd /connectors || exit 0

# если файлов нет – выходим подчёркнуто тихо
set -- *.json
[ "$1" = '*.json' ] && { echo '⚠  no json found'; exit 0; }

for f in "$@"; do
  name="${f%.json}"
  echo "• $name"
  curl -s -o /dev/null -X DELETE \
       "http://kafka-connect:8083/connectors/$name"
  curl -s -w '  → HTTP %{http_code}\n' -o /dev/null \
       -X POST -H 'Content-Type: application/json' \
       --data "@$f" \
       "http://kafka-connect:8083/connectors"
done
echo '✔ done'
