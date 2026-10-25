"""Summarize and validate the organism-v6 H010 leaderboard pair."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "dynamics_energy_ratio": (159, "candidates/dynamics_energy_ratio/principle_organism.py"),
    "dynamics_energy_ratio_ablation": (
        160,
        "candidates/dynamics_energy_ratio_ablation/principle_organism.py",
    ),
}


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


found = {}
with (ROOT / "sandbox/leaderboard.jsonl").open() as source:
    for row_number, line in enumerate(source, 1):
        row = json.loads(line)
        name = row.get("candidate")
        if name not in TARGETS:
            continue
        size = row["sizes"][0]
        rooms = size["summary"]["rooms_reached"]
        path = TARGETS[name][1]
        found[name] = {
            "row": row_number,
            "candidate": name,
            "author": row["author"],
            "score": row["score"],
            "rooms_mean": rooms["mean"],
            "rooms_ci95": rooms["ci95"],
            "protocol": {
                "version": row["protocol"]["version"],
                "steps": row["protocol"]["steps"],
                "worlds": row["protocol"]["worlds_per_calibration"],
                "sensors": row["protocol"]["sensors"],
                "interoception": row["interoception"],
            },
            "structure_final": size["growth"]["final"],
            "record_sha256": row["principle_sha256"],
            "current_file_sha256": digest(path),
        }

assert set(found) == set(TARGETS), f"missing pair: {set(TARGETS) - set(found)}"
for name, (expected_row, _) in TARGETS.items():
    assert found[name]["row"] == expected_row, (name, found[name]["row"])
    assert found[name]["record_sha256"] == found[name]["current_file_sha256"], name

base = found["dynamics_energy_ratio"]
ablation = found["dynamics_energy_ratio_ablation"]
assert base["protocol"] == ablation["protocol"]
delta = base["rooms_mean"] - ablation["rooms_mean"]
overlap = max(base["rooms_ci95"][0], ablation["rooms_ci95"][0]) <= min(
    base["rooms_ci95"][1], ablation["rooms_ci95"][1]
)
assert overlap and delta < 0, "H010 falsifier not met"

print(json.dumps({"base": base, "ablation": ablation, "delta_base_minus_ablation": delta,
                  "ci95_overlap": overlap, "h010_v6_prediction_falsified": True}, indent=2))
