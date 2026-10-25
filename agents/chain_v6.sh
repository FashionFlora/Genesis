#!/bin/bash
# przebudowa drabiny pokoi (organism-v6) w turach aż KONIEC, potem automat startu agentów (sprawdza testy i kalibrację)
G=/opt/dlami/nvme/genesis; cd $G
sed -i '/^KONIEC$/d' HANDOFF.md
for i in $(seq 1 12); do
  while tmux has-session -t =genesis-sedzia 2>/dev/null; do sleep 30; done
  [ $i -gt 1 ] && grep -qx "KONIEC" HANDOFF.md && break
  { cat agents/prompts_world_v6.txt; [ $i -gt 1 ] && printf '\nKontynuacja: przeczytaj HANDOFF.md i rób dalej od miejsca, w którym skończyłeś.\n'; } > logs/world_prompt.txt
  tmux new-session -d -s genesis-sedzia "cd $G && nice -n 15 $HOME/.local/bin/codex3 exec \"\$(cat logs/world_prompt.txt)\" --json --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -C $G < /dev/null >> logs/world.jsonl 2>> logs/world.err; echo EXIT \$? >> logs/world.err"
  sleep 60
done
.venv/bin/python agents/autostart_gate.py
