#!/usr/bin/env bash
# Kopiuje stan projektu GENESIS do repozytorium gita (bez venv, cache, logów i plików >5 MB) i robi commit + push.
# Obecny system -> katalog główny; faza 1 (archiwum sprzed resetu) -> archive/phase1; archeolog -> archive/archeology.
set -e
SRC=/opt/dlami/nvme/genesis; DST=/opt/dlami/nvme/genesis_repo; ARC=/opt/dlami/nvme/genesis_archive
COMMON=(--max-size=5m --exclude .venv --exclude cache --exclude logs --exclude __pycache__ --exclude '*.pyc'
        --exclude registry/sources --exclude run.jsonl --exclude run.err --exclude cont_prompt.txt)
rsync -a --delete "${COMMON[@]}" --exclude .git --exclude README.md --exclude .gitignore --exclude docs \
  --exclude archive --exclude /HANDOFF.md --exclude run_area.sh --exclude supervisor.py "$SRC"/ "$DST"/
mkdir -p "$DST/archive"
# fazy: 1 = strumienie (do resetu 23.10 11:53), 2 = czysty start na strumieniach (20 min), 3 = pierwszy świat organizmów (v2)
for pair in "2026-10-23_reset:phase1" "2026-10-23_phase2:phase2" "2026-10-23_phase3:phase3"; do
  src="${pair%%:*}"; dst="${pair##*:}"
  [ -d "$ARC/$src" ] && rsync -a --delete "${COMMON[@]}" --exclude /HANDOFF.md --exclude run_area.sh --exclude supervisor.py \
    "$ARC/$src"/ "$DST/archive/$dst"/
done
[ -d "$ARC/archeology" ] && rsync -a --delete "${COMMON[@]}" --exclude sandbox "$ARC/archeology"/ "$DST/archive/archeology"/
cd "$DST"
git add -A
git commit -q -m "${1:-Stan projektu $(date '+%Y-%m-%d %H:%M')}" && git push -q origin HEAD 2>&1 | tail -2 || echo "brak zmian"
