#!/bin/bash
# budowa testu permutacji i --quick w turach, aż spełnione twarde warunki (nie ufa samej linii KONIEC)
G=/opt/dlami/nvme/genesis; cd $G
done_p() {
  grep -qx "KONIEC" HANDOFF.md || return 1
  grep -q -- '--quick' sandbox/judge.py || return 1
  grep -rqi "permut" sandbox/organism_judge*.py sandbox/worlds/ 2>/dev/null || return 1
  return 0
}
sed -i '/^KONIEC$/d' HANDOFF.md
for i in $(seq 1 10); do
  while tmux has-session -t =genesis-sedzia 2>/dev/null; do sleep 30; done
  [ $i -gt 1 ] && done_p && { echo "$(date '+%F %T') permutacja + quick gotowe" >> logs/autostart.log; exit 0; }
  sed -i '/^KONIEC$/d' HANDOFF.md
  { cat agents/prompts_world_permute.txt; [ $i -gt 1 ] && printf '\nKontynuacja: przeczytaj HANDOFF.md i rób dalej.\n'; } > logs/world_prompt.txt
  tmux new-session -d -s genesis-sedzia "cd $G && nice -n 15 $HOME/.local/bin/codex3 exec \"\$(cat logs/world_prompt.txt)\" --json --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -C $G < /dev/null >> logs/world.jsonl 2>> logs/world.err; echo EXIT \$? >> logs/world.err"
  sleep 60
done
