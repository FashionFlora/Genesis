"""Counterfactual probe for whether reserve-coupled retention controls action."""

import hashlib
import importlib.util
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "candidates/dynamics_metabolic_retention/principle_organism.py"


def load():
    spec = importlib.util.spec_from_file_location("retention_probe", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stream(steps=2048):
    rows = []
    for t in range(steps):
        x = torch.zeros(1, 49)
        color = (t // 64) % 3
        pixel = 3 + (t * 7) % 13
        x[0, pixel * 3 + color] = 0.8
        x[0, ((pixel + 1) % 16) * 3 + color] = 0.2
        x[0, -1] = (0.15, 0.85)[(t // 32) % 2]
        rows.append(x)
    return rows


def run(module, sensors, coupling):
    brain = module.OrganismBrain(
        302, 49, 3, 1, "cpu", seed=7,
        params={"energy_coupling": coupling},
    )
    actions = []
    for x in sensors:
        actions.append(brain.act(x).detach().clone())
    return brain, torch.cat(actions)


def main():
    module = load()
    sensors = stream()
    full, actions_full = run(module, sensors, 0.75)
    fixed, actions_fixed = run(module, sensors, 0.0)
    delta = (actions_full - actions_fixed).abs()
    report = {
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "steps": len(sensors),
        "full_vs_fixed_action_fraction_rows_changed": float((delta.max(dim=1).values > 1e-7).float().mean()),
        "full_vs_fixed_action_rmse": float(delta.square().mean().sqrt()),
        "full_vs_fixed_action_max_abs": float(delta.max()),
        "preference_state_max_abs_delta": float((full.preference - fixed.preference).abs().max()),
        "eligibility_state_max_abs_delta": float((full.eligibility - fixed.eligibility).abs().max()),
        "full_bite_count": int(actions_full[:, 2].sum()),
        "full_bites_off_age_mod_5": int(actions_full[torch.arange(len(sensors)) % 5 != 0, 2].sum()),
        "fixed_bite_count": int(actions_fixed[:, 2].sum()),
        "fixed_bites_off_age_mod_5": int(actions_fixed[torch.arange(len(sensors)) % 5 != 0, 2].sum()),
        "structure": full.structure(),
    }
    out = ROOT / "audit/metabolic_retention_coupling_probe.result.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
