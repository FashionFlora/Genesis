#!/bin/bash
# po zmianie ruchu (genesis-chain): budowa narzędzia ewolucji, aż KONIEC; potem wpis do karty
G=/opt/dlami/nvme/genesis; cd $G
while tmux has-session -t genesis-chain 2>/dev/null; do sleep 30; done
while tmux has-session -t genesis-sedzia 2>/dev/null; do sleep 30; done
sed -i '/^KONIEC$/d' HANDOFF.md
for i in $(seq 1 12); do
  while tmux has-session -t genesis-sedzia 2>/dev/null; do sleep 30; done
  [ $i -gt 1 ] && grep -qx "KONIEC" HANDOFF.md && break
  cp agents/prompts_evolve.txt logs/world_prompt.txt
  tmux new-session -d -s genesis-sedzia "cd $G && nice -n 15 $HOME/.local/bin/codex3 exec \"\$(cat logs/world_prompt.txt)\" --json --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -C $G < /dev/null >> logs/world.jsonl 2>> logs/world.err; echo EXIT \$? >> logs/world.err"
  sleep 60
done
if [ -f sandbox/evolve.py ] && ! grep -q "evolve.py" CLAUDE.md; then
python3 - <<'PY'
p='/opt/dlami/nvme/genesis/CLAUDE.md'; t=open(p).read()
t=t.replace("**Token economy:**","""**Evolution:** you may write a principle as a family with open parts (`family.py`, contract in sandbox/README.md) and let
`sandbox/evolve.py` search thousands of its versions on the GPU; selection acts only between generations, never within
a life. The evolved version must still pass the normal judge.

**Token economy:**""",1)
open(p,'w').write(t)
PY
fi
