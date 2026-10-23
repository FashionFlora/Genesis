"""Independent seed replication of adaptive_contact_flux phase probe."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from theory.theorist_growth.phase_probe import run


SEED = 1931
result = {
    "candidate": "adaptive_contact_flux",
    "replication": "independent_seed",
    "seed": SEED,
    "runs": [run(width, seed=SEED) for width in (8, 16, 32, 64)],
}

path = Path(__file__).with_name("eksperymentator_adaptive_contact_replay.json")
path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
for item in result["runs"]:
    rich, simple = item["phases"]
    print(
        f"width={item['width']} rich_edges={rich['end_connections']} "
        f"simple_edges={simple['end_connections']} "
        f"rich_brier={rich['mean_brier']:.4f} simple_brier={simple['mean_brier']:.4f}"
    )
print(f"result={path}")
