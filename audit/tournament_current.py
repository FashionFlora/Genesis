"""Pairwise audit of the two current organism leaders.

This is deliberately a mechanism audit, not a replacement for the judge.
"""
import importlib.util
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).parents[1]))
from sandbox.organism_judge import run_life, _summary
from sandbox.worlds.organism import OrganismWorld


ROOT = Path(__file__).parents[1]
NAMES = ("metabolic_gate_fixed_speed", "axiom_causal_homeostasis")


def load(name, sensors=49, batch=1):
    path = ROOT / "candidates" / name / "principle_organism.py"
    spec = importlib.util.spec_from_file_location("audit_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.OrganismBrain(302, sensors, 3, batch, "cpu", 0)


def eye(energy, color=0, pixels=16):
    x = torch.zeros(1, pixels * 3 + 1)
    x[0, color] = 1.0
    x[0, -1] = energy
    return x


def mechanism(name):
    actions = {}
    for energy in (0.1, 0.5, 0.9):
        b = load(name)
        actions[str(energy)] = [round(float(v), 6) for v in b.act(eye(energy))[0]]

    b = load(name)
    b.act(eye(0.8))
    b.act(eye(0.95))
    gain_trace = [round(float(v), 6) for v in b.trace[0]]
    b.act(eye(0.70))
    loss_trace = [round(float(v), 6) for v in b.trace[0]]

    # The no-interoception contract supplies 48 eye channels, with no energy.
    no_intero = load(name, sensors=48)
    no_intero_action = [round(float(v), 6) for v in no_intero.act(torch.zeros(1, 48))[0]]
    return {"energy_actions": actions, "trace_after_gain": gain_trace,
            "trace_after_loss": loss_trace, "no_intero_zero_action": no_intero_action,
            "structure": no_intero.structure()}


def short_world(name):
    brain = load(name, batch=8)
    row = run_life(brain, 8, "cpu", 91, interoception=True, steps=600, n_units=302)
    s = _summary([row], 302)
    return {"rooms": s["rooms_reached"]["mean"],
            "survival": s["survival"]["mean"],
            "reversal_latency": s["reversal_latency"]["mean"],
            "mean_energy": s["mean_energy"]["mean"]}


if __name__ == "__main__":
    for name in NAMES:
        print(json.dumps({"candidate": name, "mechanism": mechanism(name),
                          "short_world": short_world(name)}, sort_keys=True))
