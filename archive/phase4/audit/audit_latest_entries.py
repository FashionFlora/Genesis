"""Summarize recent organism claims against recorded protocol and source code."""

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
WATCH = {
    "metabolic_gate_fixed_speed",
    "axiom_causal_homeostasis",
    "action_consequence",
    "causal_homeostasis_replica",
    "axiom_signed_ema",
    "metabolic_gate_optional_intero",
    "metabolic_action_tag",
}

rows = [json.loads(line) for line in (ROOT / "sandbox/leaderboard.jsonl").read_text().splitlines() if line]
selected = [row for row in rows[-30:] if row.get("candidate") in WATCH and row.get("track") == "organism"]
print(f"recent_watch_records={len(selected)}")
for row in selected:
    runs = row.get("sizes", [])
    run = next((item for item in runs if item.get("units") == 302), runs[0] if runs else {})
    summary = run.get("summary", {})
    rooms = summary.get("room_reach_fraction", [])
    room2 = rooms[1].get("mean") if len(rooms) > 1 else None
    growth = run.get("growth", {})
    initial = growth.get("initial", {})
    final = growth.get("final", {})
    print(
        f"{row.get('candidate')}: score={row.get('score')} intero={row.get('interoception')} "
        f"room2={room2} units={initial.get('units')}->{final.get('units')} "
        f"connections={initial.get('connections')}->{final.get('connections')} "
        f"clone_of={row.get('clone_of')}"
    )

for name in sorted(WATCH):
    path = ROOT / "candidates" / name / "principle_organism.py"
    if not path.exists():
        continue
    source = path.read_text()
    flags = []
    if "(n_sensors - 1) // 3" in source:
        flags.append("assumes_49_sensor_shape")
    if "sensors[:, -1]" in source:
        if "has_energy = n_sensors % 3 == 1" in source and "if self.has_energy" in source:
            flags.append("last_sensor_as_energy_only_when_49")
        else:
            flags.append("last_sensor_as_energy_without_shape_guard")
    if "torch.zeros(batch, 3" in source:
        flags.append("fixed_three_categories")
    if '"slow_speed"' in source and '"fed_speed"' in source:
        flags.append("energy_modulated_speed")
    print(f"source {name}: {','.join(flags) or 'no_watch_pattern'}")
