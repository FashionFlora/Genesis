#!/bin/bash
# po zakończeniu bieżącej budowy świata: tury sprzątania długu technicznego, aż HANDOFF.md ma linię KONIEC (max 10)
G=/opt/dlami/nvme/genesis; cd $G
while tmux has-session -t genesis-world-loop 2>/dev/null; do sleep 30; done
while tmux has-session -t genesis-sedzia 2>/dev/null; do sleep 30; done
sed -i '/^KONIEC$/d' HANDOFF.md
for i in $(seq 1 10); do
  while tmux has-session -t genesis-sedzia 2>/dev/null; do sleep 30; done
  [ $i -gt 1 ] && grep -qx "KONIEC" HANDOFF.md && exit 0
  cp agents/prompts_world_cleanup.txt logs/world_prompt.txt
  tmux new-session -d -s genesis-sedzia "cd $G && nice -n 15 $HOME/.local/bin/codex3 exec \"\$(cat logs/world_prompt.txt)\" --json --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -C $G < /dev/null >> logs/world.jsonl 2>> logs/world.err; echo EXIT \$? >> logs/world.err"
  sleep 60
done
