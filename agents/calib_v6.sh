#!/bin/bash
# kalibracja organism-v6: 5 kontroli równolegle (sloty GPU), złożenie tabeli końcowej, potem automat startu agentów
G=/opt/dlami/nvme/genesis; cd $G; mkdir -p logs/calib_v6
for m in random braitenberg delta table growing; do
  nice -n 15 .venv/bin/python sandbox/judge.py candidates/_organism_random --organism --organism-baseline $m \
    --organism-seeds 1 --author calibration > logs/calib_v6/$m.json 2> logs/calib_v6/$m.err &
done
wait
.venv/bin/python - <<'PY'
import json, time
G = "/opt/dlami/nvme/genesis"
rows = {}
for l in open(f"{G}/sandbox/organism_calibration.jsonl"):
    try:
        d = json.loads(l)
    except json.JSONDecodeError:
        continue
    p = d.get("protocol") or {}
    if isinstance(p, dict) and p.get("version") == "organism-v6" and d.get("baseline") in ("random", "braitenberg", "delta", "table", "growing") and d.get("sizes"):
        rows[d["baseline"]] = (d["sizes"][0]["summary"], p)
missing = {"random", "braitenberg", "delta", "table", "growing"} - set(rows)
if missing:
    print("BRAK", sorted(missing)); raise SystemExit(1)
table = {k: v[0] for k, v in rows.items()}
sep = [{"room": r + 1, "positive_lower": table["growing"]["room_reach_fraction"][r]["ci95"][0],
        "negative_upper": table["table"]["room_reach_fraction"][r]["ci95"][1]} for r in range(1, len(table["growing"]["room_reach_fraction"]))]
for s in sep:
    s["disjoint"] = s["positive_lower"] > s["negative_upper"]
row = {"track": "organism_calibration", "candidate": "organism-v6-final", "author": "calibration",
       "baseline": "baseline_table", "baseline_table": table, "new_room_ci_separation": sep,
       "protocol": rows["growing"][1], "assembled_from_separate_runs": True, "time": time.strftime("%Y-%m-%d %H:%M")}
open(f"{G}/sandbox/organism_calibration.jsonl", "a").write(json.dumps(row) + "\n")
for k, v in table.items():
    print(k, [round(x["mean"], 3) for x in v["room_reach_fraction"]])
print("separation", [(s["room"], s["disjoint"]) for s in sep])
PY
.venv/bin/python agents/autostart_gate.py
