#!/usr/bin/env bash
# Kopiuje stan projektu GENESIS do repozytorium gita (bez venv, cache, logów i plików >5 MB) i robi commit + push.
set -e
SRC=/opt/dlami/nvme/genesis; DST=/opt/dlami/nvme/genesis_repo
rsync -a --delete --max-size=5m \
  --exclude .git --exclude README.md --exclude .gitignore --exclude docs \
  --exclude .venv --exclude shared/cache --exclude logs --exclude __pycache__ --exclude '*.pyc' \
  --exclude registry/sources --exclude HANDOFF.md --exclude run_area.sh --exclude supervisor.py \
  "$SRC"/ "$DST"/
# HANDOFF.md agentów (pamięć między turami) zostawiamy, pomijamy tylko luźny w katalogu głównym
for f in $(cd "$SRC" && find . -path ./.venv -prune -o -name HANDOFF.md -print | grep -v '^./HANDOFF.md$'); do
  mkdir -p "$DST/$(dirname "$f")"; cp "$SRC/$f" "$DST/$f"; done
cd "$DST"
git add -A
git commit -q -m "${1:-Stan projektu $(date '+%Y-%m-%d %H:%M')}" && git push -q origin HEAD 2>&1 | tail -2 || echo "brak zmian"
