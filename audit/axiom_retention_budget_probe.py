"""Causal/provenance probe for leaderboard rows 175 and 178."""
import importlib.util
import json
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.OrganismBrain


def run(cls, stream, units=302, params=None):
    b = cls(units, stream.shape[-1], 3, stream.shape[1], "cpu", seed=31, params=params)
    acts = torch.stack([b.act(frame).detach() for frame in stream])
    return acts, b


def rmse(a, b):
    return float((a - b).square().mean().sqrt())


def plain(x):
    if isinstance(x, torch.Tensor):
        return x.detach().cpu().tolist()
    if isinstance(x, dict):
        return {k: plain(v) for k, v in x.items()}
    return x


def main():
    Main = load("candidates/axiom_metabolic_retention_budget/principle_organism.py", "main")
    Control = load("candidates/axiom_metabolic_retention_budget_ablation/principle_organism.py", "control")
    g = torch.Generator().manual_seed(731)
    stream = torch.rand(96, 64, 49, generator=g)
    nominal, bm = run(Main, stream)
    control, bc = run(Control, stream)
    no_coupling, bn = run(Main, stream, params={"energy_coupling": 0.0})
    no_learning, bl = run(Main, stream, params={"learning_rate": 0.0})

    flipped = stream.clone()
    flipped[:, :, 48] = 1.0 - flipped[:, :, 48]
    energy_flip, _ = run(Main, flipped)
    rgb = stream[:, :, :48]
    no_i, bni = run(Main, rgb)
    neutral = stream.clone()
    neutral[:, :, 48] = 0.5
    neutral_i, _ = run(Main, neutral)

    bright = torch.zeros(32, 64, 49)
    bright[:, :, 24] = 1.0
    bright[:, :, 48] = 0.5
    bright_main, _ = run(Main, bright)
    bright_control, _ = run(Control, bright)
    large, blarge = run(Main, stream, units=100000)
    source = (ROOT / "candidates/axiom_metabolic_retention_budget/principle_organism.py").read_text()
    out = {
        "random_main_vs_control": {"action_rmse": rmse(nominal, control), "max_abs": float((nominal - control).abs().max())},
        "component_controls": {
            "energy_coupling_zero_rmse": rmse(nominal, no_coupling),
            "learning_rate_zero_rmse": rmse(nominal, no_learning),
            "preference_max": float(bm.preference.abs().max()),
            "control_preference_max": float(bc.preference.abs().max()),
            "no_coupling_preference_max": float(bn.preference.abs().max()),
            "no_learning_preference_max": float(bl.preference.abs().max()),
        },
        "interoception": {
            "energy_flip_rmse": rmse(nominal, energy_flip),
            "no_energy_vs_neutral_rmse": rmse(no_i, neutral_i),
        },
        "bright_fixed_scene": {
            "main_vs_control_rmse": rmse(bright_main, bright_control),
            "main_bites": float(bright_main[:, :, 2].sum()),
            "control_bites": float(bright_control[:, :, 2].sum()),
        },
        "scaling": {
            "action_rmse_302_vs_100000": rmse(nominal, large),
            "structure_302": plain(bm.structure()),
            "structure_100000": plain(blarge.structure()),
        },
        "source_flags": {
            "fixed_eye_offset": "eye[:, 4:]" in source,
            "green_parity_context": "0::2" in source and "1::2" in source,
            "periodic_bite_gate": "remainder(5)" in source,
            "energy_used_for_retention_and_urgency": True,
        },
    }
    path = ROOT / "audit/axiom_retention_budget_probe.result.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
