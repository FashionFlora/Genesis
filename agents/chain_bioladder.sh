#!/bin/bash
# po starcie agentów na v6 (koniec genesis-chain-v6): budowa drabiny biologicznej v7 w tle, aż KONIEC
G=/opt/dlami/nvme/genesis; cd $G
while tmux has-session -t =genesis-chain-v6 2>/dev/null; do sleep 60; done
tmux has-session -t =genesis-supervisor 2>/dev/null || { echo "$(date) agenci nie wystartowali na v6, drabina v7 czeka" >> logs/autostart.log; exit 0; }
while tmux has-session -t =genesis-sedzia 2>/dev/null; do sleep 30; done
sed -i '/^KONIEC$/d' HANDOFF.md
for i in $(seq 1 12); do
  while tmux has-session -t =genesis-sedzia 2>/dev/null; do sleep 30; done
  [ $i -gt 1 ] && grep -qx "KONIEC" HANDOFF.md && break
  { cat agents/prompts_world_bioladder.txt; [ $i -gt 1 ] && printf '\nKontynuacja: przeczytaj HANDOFF.md i rób dalej.\n'; } > logs/world_prompt.txt
  tmux new-session -d -s genesis-sedzia "cd $G && nice -n 15 $HOME/.local/bin/codex3 exec \"\$(cat logs/world_prompt.txt)\" --json --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -C $G < /dev/null >> logs/world.jsonl 2>> logs/world.err; echo EXIT \$? >> logs/world.err"
  sleep 60
done
