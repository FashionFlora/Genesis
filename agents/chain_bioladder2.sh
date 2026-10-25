#!/bin/bash
# kolejne tury budowy v7 aż do spełnienia twardych warunków (nie ufa linii KONIEC)
G=/opt/dlami/nvme/genesis; cd $G
done_v7() {
  grep -q '"organism-v7-final"' sandbox/organism_calibration.jsonl 2>/dev/null || return 1
  grep -A1 '"--organism-version"' sandbox/judge.py | grep -q 'default="v7"\|default="organism-v7"' || return 1
  timeout 1200 nice -n 15 .venv/bin/python sandbox/test_organism.py > logs/v7_tests.out 2>&1 || return 1
  return 0
}
for i in $(seq 1 15); do
  while tmux has-session -t =genesis-sedzia 2>/dev/null; do sleep 30; done
  done_v7 && { echo "$(date '+%F %T') v7 gotowe wg warunków" >> logs/autostart.log; exit 0; }
  sed -i '/^KONIEC$/d' HANDOFF.md
  { cat agents/prompts_world_bioladder.txt; printf '\nKontynuacja: przeczytaj HANDOFF.md i rób dalej.\n'; } > logs/world_prompt.txt
  tmux new-session -d -s genesis-sedzia "cd $G && nice -n 15 $HOME/.local/bin/codex3 exec \"\$(cat logs/world_prompt.txt)\" --json --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -C $G < /dev/null >> logs/world.jsonl 2>> logs/world.err; echo EXIT \$? >> logs/world.err"
  sleep 60
done
echo "$(date '+%F %T') v7: 15 tur bez spełnienia warunków" >> logs/autostart.log
