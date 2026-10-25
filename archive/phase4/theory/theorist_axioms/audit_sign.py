"""Paired mechanism test: signed trace versus gain-only trace."""
import importlib.util
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from sandbox.organism_judge import run_life, _summary

SOURCE = ROOT / "candidates/axiom_causal_homeostasis/principle_organism.py"


def load(positive_only):
    source = SOURCE.read_text()
    if positive_only:
        old = 'delta * self.params["loss_deposit"]'
        source = source.replace(old, 'torch.zeros_like(delta)')
    namespace = {"__name__": "audit_positive" if positive_only else "audit_signed"}
    exec(compile(source, str(SOURCE), "exec"), namespace)
    return namespace["OrganismBrain"](302, 49, 3, 8, "cpu", seed=0)


def measure(positive_only):
    brain = load(positive_only)
    row = run_life(brain, 8, "cpu", 20261024, interoception=True,
                   steps=6000, n_units=302)
    summary = _summary([row], 302)
    return {key: summary[key]["mean"] for key in
            ("rooms_reached", "survival", "mean_energy", "reversal_latency")}


if __name__ == "__main__":
    print(json.dumps({"steps": 6000, "batch": 8,
                      "signed": measure(False),
                      "gain_only_ablation": measure(True)}, sort_keys=True))
