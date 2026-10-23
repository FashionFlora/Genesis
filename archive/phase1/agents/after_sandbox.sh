#!/usr/bin/env bash
# Czeka, aż budowniczy skończy bieżącą turę, i wznawia go z zadaniem drabiny.
cd /opt/dlami/nvme/genesis
while tmux has-session -t genesis-sandbox 2>/dev/null; do sleep 30; done
tid=$(head -1 logs/v3_sandbox.jsonl | python3 -c "import sys,json;print(json.loads(sys.stdin.read())['thread_id'])")
tmux new-session -d -s genesis-sandbox "cd /opt/dlami/nvme/genesis && nice -n 15 $HOME/.local/bin/codex2 exec resume $tid \"\$(cat agents/prompts_v3_ladder.txt)\" --json --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check < /dev/null >> logs/v3_sandbox.jsonl 2>> logs/v3_sandbox.err; echo EXIT \$? >> logs/v3_sandbox.err"
echo "drabina zlecona $(date +%H:%M)"
