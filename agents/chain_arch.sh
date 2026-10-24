#!/bin/bash
# po zmianie ruchu (genesis-chain): tury pokoi wymagających architektury, aż KONIEC; potem ogłoszenie
G=/opt/dlami/nvme/genesis; cd $G
while tmux has-session -t genesis-chain 2>/dev/null || tmux has-session -t genesis-chain-evo 2>/dev/null; do sleep 30; done
while tmux has-session -t genesis-sedzia 2>/dev/null; do sleep 30; done
sed -i '/^KONIEC$/d' HANDOFF.md
for i in $(seq 1 12); do
  while tmux has-session -t genesis-sedzia 2>/dev/null; do sleep 30; done
  [ $i -gt 1 ] && grep -qx "KONIEC" HANDOFF.md && break
  cp agents/prompts_world_arch.txt logs/world_prompt.txt
  tmux new-session -d -s genesis-sedzia "cd $G && nice -n 15 $HOME/.local/bin/codex3 exec \"\$(cat logs/world_prompt.txt)\" --json --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -C $G < /dev/null >> logs/world.jsonl 2>> logs/world.err; echo EXIT \$? >> logs/world.err"
  sleep 60
done
python3 shared/board.py post orchestrator all "Świat organizmów ma nowe dalsze pokoje (organism-v5): wiele rodzajów obiektów, nowe w trakcie życia, znaczenie zależne od kontekstu, pamięć miejsc poza zasięgiem wzroku. Stała mała tabela wag je oblewa (kontrola negatywna), a uczeń z rosnącą pamięcią przechodzi (kontrola pozytywna). Przelicz swoich kandydatów; szczegóły sandbox/README.md i sandbox/organism_calibration.jsonl."
