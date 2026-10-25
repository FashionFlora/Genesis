"""Audit row 172 and its row-170 sensorimotor-prediction parent."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.OrganismBrain


def run(cls, n_units=302, sensors=49, batch=16, steps=96, seed=19, params=None):
    g = torch.Generator().manual_seed(303)
    stream = torch.rand(steps, batch, sensors, generator=g)
    brain = cls(n_units, sensors, 3, batch, "cpu", seed=seed, params=params)
    acts = torch.stack([brain.act(x).detach() for x in stream])
    return acts, brain


def j(x):
    if isinstance(x, torch.Tensor):
        return x.detach().cpu().tolist()
    if isinstance(x, dict):
        return {k: j(v) for k, v in x.items()}
    return x


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parent_path = ROOT / "candidates/agency_sensorimotor_prediction/principle_organism.py"
    ablation_path = ROOT / "candidates/agency_sensorimotor_prediction_ablation/principle_organism.py"
    Parent = load(parent_path, "agency_prediction_parent")
    Ablation = load(ablation_path, "agency_prediction_ablation")

    parent, bp = run(Parent)
    control, bc = run(Ablation)
    gain0, bg = run(Parent, params={"prediction_gain": 0.0})
    parent_large, bl = run(Parent, n_units=100000)

    # Energy is the final sensor in the judge's 49-sensor interface. The source
    # slices only the first 48 into RGB pixels, so this tests whether it matters.
    g = torch.Generator().manual_seed(404)
    stream = torch.rand(32, 8, 49, generator=g)
    altered = stream.clone()
    altered[:, :, 48] = 1.0 - altered[:, :, 48]
    b1 = Parent(302, 49, 3, 8, "cpu", seed=23)
    b2 = Parent(302, 49, 3, 8, "cpu", seed=23)
    a1 = torch.stack([b1.act(x).detach() for x in stream])
    a2 = torch.stack([b2.act(x).detach() for x in altered])

    out = {
        "source_sha256": {"parent": sha(parent_path), "ablation": sha(ablation_path)},
        "recorded_row_172_sha256": "34d5ba4d953e1f156b8a18cb8a15f6ccc0e6d1a1f8b39da856dc9b151a60c9c2",
        "parent_vs_ablation": {
            "action_rmse": float((parent - control).square().mean().sqrt()),
            "action_max_abs": float((parent - control).abs().max()),
            "state_predicted_delta_max_abs": float((bp.predicted_delta - bc.predicted_delta).abs().max()),
            "parent_structure": j(bp.structure()),
            "ablation_structure": j(bc.structure()),
        },
        "ablation_matches_parent_gain_zero": {
            "action_rmse": float((control - gain0).square().mean().sqrt()),
            "action_max_abs": float((control - gain0).abs().max()),
            "structure_max_abs": float((torch.as_tensor(bc.structure()["connections"]) - torch.as_tensor(bg.structure()["connections"])).abs().max()),
        },
        "scaling": {
            "action_rmse_302_vs_100000": float((parent - parent_large).square().mean().sqrt()),
            "structure_302": j(bp.structure()),
            "structure_100000": j(bl.structure()),
        },
        "energy_sensor_last_column": {
            "action_rmse": float((a1 - a2).square().mean().sqrt()),
            "action_max_abs": float((a1 - a2).abs().max()),
        },
        "source_flags": {
            "uses_energy_sensor": "energy" in parent_path.read_text().lower(),
            "strongest_channel_argmax": "argmax" in parent_path.read_text(),
            "fixed_thresholds": ["> 0.10", "> 1.25", "> 0.22"],
            "sinusoidal_exploration": "sin(" in parent_path.read_text(),
            "hardcoded_eye_prefix": "x[:, :self.eye_width * 3]" in parent_path.read_text(),
        },
    }
    result = ROOT / "audit/agency_prediction_ablation_audit.result.json"
    result.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
