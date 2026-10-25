"""Matched organism ablation of adaptive link pruning."""
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from sandbox.organism_judge import run_life, _summary

SOURCE = ROOT / "candidates/axiom_causal_sparse_growth/principle_organism.py"


def measure(pruning):
    namespace = {"__name__": f"sparse_pruning_{pruning}"}
    exec(compile(SOURCE.read_text(), str(SOURCE), "exec"), namespace)
    Brain = namespace["OrganismBrain"]
    params = {} if pruning else {"prune_use": -1.0}
    brain = Brain(302, 49, 3, 8, "cpu", seed=0, params=params)
    row = run_life(brain, 8, "cpu", 20261024, interoception=True,
                   steps=6000, n_units=302)
    summary = _summary([row], 302)
    return {key: summary[key]["mean"] for key in
            ("rooms_reached", "survival", "mean_energy", "reversal_latency")}


if __name__ == "__main__":
    print(json.dumps({"steps": 6000, "batch": 8,
                      "pruning_on": measure(True),
                      "pruning_off": measure(False)}, sort_keys=True))
