#!/usr/bin/env bash
cd /opt/dlami/nvme/genesis
while tmux has-session -t genesis-sedzia 2>/dev/null; do sleep 30; done
tid=$(head -1 logs/v3_sedzia.jsonl | python3 -c "import sys,json;print(json.loads(sys.stdin.read())['thread_id'])")
tmux new-session -d -s genesis-sedzia "cd /opt/dlami/nvme/genesis && nice -n 15 $HOME/.local/bin/codex3 exec resume $tid \"\$(cat agents/prompts_v3_grok.txt)\" --json --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check < /dev/null >> logs/v3_sedzia.jsonl 2>> logs/v3_sedzia.err; echo EXIT \$? >> logs/v3_sedzia.err"
echo "grok zlecony $(date +%H:%M)"
