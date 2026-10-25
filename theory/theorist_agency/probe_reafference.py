"""Controlled action-consequence probe for agency_reafferent_turn."""

import importlib.util
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[2]


def load(name):
    path = ROOT / "candidates" / name / "principle_organism.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.OrganismBrain(302, 49, 3, 4, "cpu", seed=17)


def eye(pixel, amount, batch=4):
    value = torch.zeros(batch, 49)
    value[:, pixel * 3:pixel * 3 + 3] = amount / 3.0
    return value


def run(brain):
    # Pixel 4 is at a positive angular bearing; pixel 12 is negative.
    observations = [eye(4, 0.8), eye(4, 1.8), eye(12, 0.2), eye(12, 1.8)]
    actions = torch.stack([brain.act(item) for item in observations])
    return actions


def main():
    main_actions = run(load("agency_reafferent_turn"))
    control_actions = run(load("agency_reafferent_turn_ablation"))
    diff = (main_actions - control_actions).abs()
    result = {
        "steps": int(main_actions.shape[0]),
        "finite": bool(torch.isfinite(main_actions).all() and torch.isfinite(control_actions).all()),
        "action_mae": float(diff.mean()),
        "max_action_difference": float(diff.max()),
        "changed_fraction": float((diff.amax(dim=2) > 1e-6).float().mean()),
        "main": main_actions.tolist(),
        "ablation": control_actions.tolist(),
    }
    path = Path(__file__).with_name("probe_reafference.result.json")
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in result if k not in ("main", "ablation")}))


if __name__ == "__main__":
    main()
