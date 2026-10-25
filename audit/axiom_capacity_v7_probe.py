"""Mechanism and scale probe for the latest axiom capacity record."""

import hashlib
import importlib.util
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "candidates/axiom_capacity_correlation/principle_organism.py"
ABLATION = ROOT / "candidates/axiom_capacity_correlation_ablation/principle_organism.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_inputs(steps=96, batch=2, sensors=49):
    rows = []
    for t in range(steps):
        x = torch.zeros(batch, sensors)
        x[:, (3 * (t % 7)) % (sensors - 1)] = 1.0
        x[:, (17 + 5 * t) % (sensors - 1)] = 0.35
        x[:, -1] = 0.2 + 0.7 * ((t % 9) / 8.0)
        rows.append(x)
    return rows


def run(module, n_units, rows):
    brain = module.OrganismBrain(n_units, 49, 3, rows[0].shape[0], "cpu", seed=11)
    actions = []
    norms = []
    for sensors in rows:
        actions.append(brain.act(sensors).detach().clone())
        norms.append(float(brain.weights.norm(dim=2).mean().item()))
    return brain, torch.stack(actions), norms


def main():
    module = load(TARGET, "capacity_v7")
    ablation = load(ABLATION, "capacity_v7_ablation")
    rows = make_inputs()
    small, a_small, norms = run(module, 302, rows)
    large, a_large, _ = run(module, 100000, rows)
    frozen, a_frozen, _ = run(ablation, 302, rows)
    report = {
        "source_sha256": hashlib.sha256(TARGET.read_bytes()).hexdigest(),
        "steps": len(rows),
        "actions_302_vs_100000_identical": bool(torch.allclose(a_small, a_large, atol=1e-7, rtol=1e-7)),
        "structure_302": small.structure(),
        "structure_100000": large.structure(),
        "mean_norm_initial_and_final": [norms[0], norms[-1]],
        "per_sensor_norm_spread_final": float((small.weights.norm(dim=2).max() - small.weights.norm(dim=2).min()).item()),
        "learned_vs_frozen_action_rmse": float(torch.mean((a_small - a_frozen) ** 2).sqrt().item()),
        "max_abs_learned_vs_frozen": float(torch.max(torch.abs(a_small - a_frozen)).item()),
    }
    out = ROOT / "audit/axiom_capacity_v7_probe.result.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
