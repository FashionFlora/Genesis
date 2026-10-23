#!/bin/bash
# kolejne tury archeologa, aż powstanie REPORT.md z linią KONIEC (max 20 tur)
cd /opt/dlami/nvme/genesis_archive/archeology
for i in $(seq 1 20); do
  while tmux has-session -t genesis-archeolog 2>/dev/null; do sleep 30; done
  grep -q "KONIEC" REPORT.md 2>/dev/null && exit 0
  P="$(cat PROMPT.txt)

Kontynuacja: przeczytaj HANDOFF.md, mechanisms.tsv i results.tsv w swoim katalogu i rób dalej od miejsca, w którym skończyłeś. Gdy przebadasz wszystkie mechanizmy i napiszesz REPORT.md, dopisz w nim ostatnią linię KONIEC."
  printf '%s' "$P" > cont_prompt.txt
  tmux new-session -d -s genesis-archeolog "cd /opt/dlami/nvme/genesis_archive/archeology && nice -n 15 /home/ubuntu/.local/bin/codex3 exec \"\$(cat cont_prompt.txt)\" --json --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -C /opt/dlami/nvme/genesis_archive/archeology < /dev/null >> run.jsonl 2>> run.err; echo EXIT \$? >> run.err"
  sleep 60
done
