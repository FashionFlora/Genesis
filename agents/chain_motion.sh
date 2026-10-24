#!/bin/bash
# po zadaniu "growth": tury zmiany ruchu (aż KONIEC), potem automat startu agentów
G=/opt/dlami/nvme/genesis; cd $G
while tmux has-session -t genesis-sedzia 2>/dev/null; do sleep 30; done
sed -i '/^KONIEC$/d' HANDOFF.md
for i in $(seq 1 10); do
  while tmux has-session -t genesis-sedzia 2>/dev/null; do sleep 30; done
  [ $i -gt 1 ] && grep -qx "KONIEC" HANDOFF.md && break
  cp agents/prompts_world_motion.txt logs/world_prompt.txt
  tmux new-session -d -s genesis-sedzia "cd $G && nice -n 15 $HOME/.local/bin/codex3 exec \"\$(cat logs/world_prompt.txt)\" --json --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -C $G < /dev/null >> logs/world.jsonl 2>> logs/world.err; echo EXIT \$? >> logs/world.err"
  sleep 60
done
python3 shared/board.py post sedzia all "Świat organizmów zaktualizowany do organism-v4: napęd ze znakiem (do przodu / stop / do tyłu), koszt energii od |prędkości|, pole growth (faktyczny rozmiar mózgu w czasie; n_units to tylko górny limit). Kontrakt mózgu bez zmian. Wyniki z v3 nie są porównywalne z v4: przelicz swoich kandydatów. Kalibracja v4 w sandbox/organism_calibration.jsonl."
