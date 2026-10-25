#!/bin/bash
# strażnik Genesis: co 10 min zapisuje anomalie do logs/health.log (tylko obserwacja, niczego nie zmienia)
G=/opt/dlami/nvme/genesis; L=$G/logs/health.log
while true; do
  t=$(date '+%d %H:%M'); p=""
  tmux has-session -t =genesis-supervisor 2>/dev/null || p+=" NADZORCA_NIE_DZIALA;"
  n=$(tmux ls -F '#{session_name}' 2>/dev/null | grep -cE '^genesis-(odkrywca|biolog|krytyk|eksperymentator)')
  [ "$n" -lt 4 ] && p+=" tylko_${n}_agentow;"
  while read -r pid et pc args; do
    s=$(echo "$et" | awk -F'[-:]' '{if(NF==4)print $1*86400+$2*3600+$3*60+$4; else if(NF==3)print $1*3600+$2*60+$3; else print $1*60+$2}')
    [ "$s" -gt 2400 ] && p+=" sedzia_${s}s_pid${pid};"
  done < <(ps -eo pid,etime,pcpu,args | grep -E "sandbox/(judge|evolve)\.py" | grep -v grep | awk '{print $1,$2,$3,$4}')
  for c in $(tmux ls -F '#{session_name}' 2>/dev/null | grep -E '^genesis-chain'); do
    tmux has-session -t =genesis-sedzia 2>/dev/null || p+=" ${c}_bez_budowniczego;"
  done
  last=$(stat -c %Y $G/shared/board.jsonl 2>/dev/null || echo 0); [ $(( $(date +%s) - last )) -gt 1800 ] && p+=" tablica_cicha_30min;"
  grep -qE '"(401|402|403)"|insufficient|paid time' <(tail -c 20000 $G/logs/v3_krytyk.jsonl 2>/dev/null) && p+=" BLAD_API;"
  df -P /opt/dlami/nvme | awk 'NR==2{if($5+0>92)print}' | grep -q . && p+=" DYSK_PELNY;"
  [ -n "$p" ] && echo "$t$p" >> $L || echo "$t ok" >> $L
  sleep 600
done
