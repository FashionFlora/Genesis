#!/bin/bash
# po zakończeniu budowy toru GPU uruchamia zadanie partii GPU dla małych światów
cd /opt/dlami/nvme/genesis
while tmux has-session -t genesis-sedzia 2>/dev/null; do sleep 30; done
tmux new-session -d -s genesis-sedzia "cd /opt/dlami/nvme/genesis && nice -n 15 $HOME/.local/bin/codex3 exec \"\$(cat agents/prompts_v3_gpubatch.txt)\" --json --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check < /dev/null > logs/v3_gpubatch.jsonl 2> logs/v3_gpubatch.err; echo EXIT \$? >> logs/v3_gpubatch.err"
