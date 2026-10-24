#!/bin/bash
# kolejne tury budowniczego świata organizmów, aż HANDOFF.md zawiera KONIEC (max 20 tur)
G=/opt/dlami/nvme/genesis; cd $G
for i in $(seq 1 20); do
  while tmux has-session -t genesis-sedzia 2>/dev/null; do sleep 30; done
  grep -qx "KONIEC" HANDOFF.md 2>/dev/null && exit 0
  { cat agents/prompts_world_fix2.txt; } > logs/world_prompt.txt
  tmux new-session -d -s genesis-sedzia "cd $G && nice -n 15 $HOME/.local/bin/codex3 exec \"\$(cat logs/world_prompt.txt)\" --json --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -C $G < /dev/null >> logs/world.jsonl 2>> logs/world.err; echo EXIT \$? >> logs/world.err"
  sleep 60
done
