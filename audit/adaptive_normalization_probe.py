"""Implementation-level controls for leaderboard row 178.

The published ablation disables every preference write.  These controls keep
the controller and its write path but remove only adaptive delta normalization
or reserve-shaped retention, so an action difference is not mislabelled as
evidence for the new term.
"""
import importlib.util
import json
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "candidates/life_metabolic_adaptive_retention_budget/principle_organism.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.OrganismBrain


def load_without_normalization(name):
    # Keep the exact source except for the proposed adaptive write term.
    text = SOURCE.read_text()
    old = "credit = (delta / self.delta_scale.clamp_min(0.01)).clamp(-1.0, 1.0)"
    new = "credit = delta.clamp(-1.0, 1.0)"
    if old not in text:
        raise RuntimeError("normalization expression changed; audit needs review")
    spec = importlib.util.spec_from_loader(name, loader=None)
    mod = importlib.util.module_from_spec(spec)
    exec(compile(text.replace(old, new), str(SOURCE), "exec"), mod.__dict__)
    return mod.OrganismBrain


def run(cls, stream, units=302, params=None):
    brain = cls(units, stream.shape[-1], 3, stream.shape[1], "cpu", seed=31, params=params)
    acts = torch.stack([brain.act(frame).detach() for frame in stream])
    return acts, brain


def rmse(a, b):
    return float((a - b).square().mean().sqrt())


def main():
    Main = load(SOURCE, "adaptive_main")
    NoNorm = load_without_normalization("adaptive_no_norm")
    g = torch.Generator().manual_seed(731)
    stream = torch.rand(96, 64, 49, generator=g)
    nominal, bmain = run(Main, stream)
    no_norm, bnorm = run(NoNorm, stream)
    no_retention, bret = run(Main, stream, params={"energy_coupling": 0.0})

    flipped = stream.clone()
    flipped[:, :, 48] = 1.0 - flipped[:, :, 48]
    flip, _ = run(Main, flipped)
    rgb, _ = run(Main, stream[:, :, :48])
    neutral = stream.clone()
    neutral[:, :, 48] = 0.5
    neutral_actions, _ = run(Main, neutral)

    bright = torch.zeros(32, 64, 49)
    bright[:, :, 24] = 1.0
    bright[:, :, 48] = 0.5
    bright_main, _ = run(Main, bright)
    bright_no_norm, _ = run(NoNorm, bright)
    large, blarge = run(Main, stream, units=100000)
    out = {
        "random_main_vs_no_normalization": {"rmse": rmse(nominal, no_norm), "max_abs": float((nominal - no_norm).abs().max())},
        "random_main_vs_no_retention_coupling": {"rmse": rmse(nominal, no_retention), "max_abs": float((nominal - no_retention).abs().max())},
        "energy_flip_rmse": rmse(nominal, flip),
        "no_energy_vs_neutral_rmse": rmse(rgb, neutral_actions),
        "bright_main_vs_no_normalization_rmse": rmse(bright_main, bright_no_norm),
        "bright_bites": {"main": float(bright_main[:, :, 2].sum()), "no_norm": float(bright_no_norm[:, :, 2].sum())},
        "scaling_rmse_302_vs_100000": rmse(nominal, large),
        "structure": {"main_302": bmain.structure(), "main_100000": blarge.structure(), "no_norm": bnorm.structure(), "no_retention": bret.structure()},
        "state": {"main_preference_max": float(bmain.preference.abs().max()), "no_norm_preference_max": float(bnorm.preference.abs().max()), "no_retention_preference_max": float(bret.preference.abs().max()), "main_delta_scale_mean": float(bmain.delta_scale.mean())},
    }
    path = ROOT / "audit/adaptive_normalization_probe.result.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
