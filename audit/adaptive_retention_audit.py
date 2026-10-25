"""Synthetic causal audit for the pending adaptive-retention organism pair."""
import importlib.util
import json
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.OrganismBrain


def run(cls, stream, n_units=302, seed=31, params=None):
    brain = cls(n_units, stream.shape[-1], 3, stream.shape[1], "cpu", seed=seed, params=params)
    actions = torch.stack([brain.act(frame).detach() for frame in stream])
    return actions, brain


def rmse(a, b):
    return float((a - b).square().mean().sqrt())


def main():
    main_path = ROOT / "candidates/life_metabolic_adaptive_retention_budget/principle_organism.py"
    control_path = ROOT / "candidates/life_metabolic_adaptive_retention_budget_ablation/principle_organism.py"
    Main = load(main_path, "adaptive_retention_main")
    Control = load(control_path, "adaptive_retention_control")
    generator = torch.Generator().manual_seed(731)
    random_stream = torch.rand(96, 64, 49, generator=generator)
    nominal, bmain = run(Main, random_stream)
    control, bcontrol = run(Control, random_stream)

    # Same RGB and different energy isolates interoceptive dependence.
    flipped = random_stream.clone()
    flipped[:, :, 48] = 1.0 - flipped[:, :, 48]
    energy_flip, _ = run(Main, flipped)
    rgb = random_stream[:, :, :48]
    no_energy, bno = run(Main, rgb)
    neutral = random_stream.clone()
    neutral[:, :, 48] = 0.5
    neutral_actions, bneutral = run(Main, neutral)

    # A fixed bright source exposes any independent periodic bite gate.
    bright = torch.zeros(32, 64, 49)
    bright[:, :, 24] = 1.0
    bright[:, :, 48] = 0.5
    bright_actions, bright_brain = run(Main, bright)
    bright_control, _ = run(Control, bright)

    large, blarge = run(Main, random_stream, n_units=100000)
    source = main_path.read_text().lower()
    out = {
        "random_main_vs_learning_zero_action_rmse": rmse(nominal, control),
        "random_main_vs_learning_zero_action_max": float((nominal - control).abs().max()),
        "preference_max": float(bmain.preference.abs().max()),
        "control_preference_max": float(bcontrol.preference.abs().max()),
        "energy_flip_action_rmse": rmse(nominal, energy_flip),
        "no_energy_vs_neutral_action_rmse": rmse(no_energy, neutral_actions),
        "no_energy_final_delta_scale": float(bno.delta_scale.mean()),
        "neutral_final_delta_scale": float(bneutral.delta_scale.mean()),
        "bright_main_vs_control_action_rmse": rmse(bright_actions, bright_control),
        "bright_main_bite_ages": [int(i) for i in torch.where(bright_actions[:, 0, 2] > 0)[0]],
        "bright_control_bite_ages": [int(i) for i in torch.where(bright_control[:, 0, 2] > 0)[0]],
        "n_units_302_vs_100000_action_rmse": rmse(nominal, large),
        "structure_302": bmain.structure(),
        "structure_100000": blarge.structure(),
        "source_flags": {
            "fixed_eye_slice": "eye[:, 4:]" in source,
            "green_parity_context": "0::2" in source and "1::2" in source,
            "periodic_age_gate": "remainder(5)" in source,
            "initial_delta_scale_005": "0.05" in source,
        },
    }
    path = ROOT / "audit/adaptive_retention_audit.result.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
