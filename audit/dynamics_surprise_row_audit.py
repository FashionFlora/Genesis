"""Deterministic mechanism probe for dynamics_surprise_retention."""

import importlib.util
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    path = ROOT / "candidates" / name / "principle_organism.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rollout(module, energy, sensor_width=49):
    generator = torch.Generator().manual_seed(7601)
    batch = 32
    brain = module.OrganismBrain(302, sensor_width, 3, batch, "cpu", seed=23)
    actions, trace_mass, surprise = [], [], []
    for value in energy:
        eye = torch.rand((batch, 48), generator=generator)
        eye[:, 0] = 0.7
        eye[:, 6] = 0.4
        sensors = torch.cat((eye, torch.full((batch, 1), value)), dim=1) if sensor_width == 49 else eye
        actions.append(brain.act(sensors).detach().clone())
        trace_mass.append(float(brain.eligibility.sum(dim=(1, 2)).mean()))
        surprise.append(float((brain.predicted_delta.abs().mean())))
    return torch.stack(actions), trace_mass, surprise, brain


def mae(left, right):
    return float((left - right).abs().mean())


def main():
    main_module = load("dynamics_surprise_retention")
    ablation_module = load("dynamics_surprise_retention_ablation")
    stable = [0.5] * 120
    expected_then_reversal = [0.5] * 58 + [0.9, 0.1] + [0.5] * 60
    main_stable = rollout(main_module, stable)
    main_reversal = rollout(main_module, expected_then_reversal)
    ablation_reversal = rollout(ablation_module, expected_then_reversal)
    no_intero = rollout(main_module, stable, sensor_width=48)
    out = {
        "scope": "deterministic implementation probe only; not organism-world evidence",
        "stable_energy_steps": len(stable),
        "reversal_energy_steps": len(expected_then_reversal),
        "trace_mass": {
            "stable_final": main_stable[1][-1],
            "reversal_before": main_reversal[1][59],
            "reversal_final": main_reversal[1][-1],
            "ablation_final": ablation_reversal[1][-1],
        },
        "action_mae": {
            "main_vs_ablation_on_reversal": mae(main_reversal[0], ablation_reversal[0]),
            "stable_vs_reversal_main": mae(main_stable[0], main_reversal[0]),
        },
        "predicted_delta_abs_final": float(main_reversal[3].predicted_delta.abs().mean()),
        "no_intero_predicted_delta_max": float(no_intero[3].predicted_delta.abs().max()),
        "source_hashes": {},
    }
    import hashlib
    for name in ("dynamics_surprise_retention", "dynamics_surprise_retention_ablation"):
        path = ROOT / "candidates" / name / "principle_organism.py"
        out["source_hashes"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    target = Path(__file__).with_suffix(".result.json")
    target.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
