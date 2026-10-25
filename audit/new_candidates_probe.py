import importlib.util
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    path = ROOT / "candidates" / name / "principle_organism.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def brain(mod, seed=7, n_units=302):
    return mod.OrganismBrain(n_units, 25, 3, 4, "cpu", seed=seed)


def stream(energy=0.5, bright=False, flip=False):
    x = torch.zeros(4, 25)
    # Eight RGB eye pixels followed by the optional energy channel.
    if bright:
        x[:, 4 * 3 + 0] = 0.9
        x[:, 4 * 3 + 1] = 0.4
    else:
        x[:, 0] = 0.25
        x[:, 7] = 0.15
    x[:, -1] = energy
    if flip:
        x[:, 1] = 0.8
        x[:, 0] = 0.0
    return x


def rollout(mod, xs, n_units=302):
    b = brain(mod, n_units=n_units)
    ys = [b.act(x).detach().clone() for x in xs]
    return torch.stack(ys)


def summary(name, mod, ablation):
    xs = [stream(0.5, bright=True) for _ in range(4)]
    main = rollout(mod, xs)
    abl = rollout(ablation, xs)
    dynamic = []
    generator = torch.Generator().manual_seed(991)
    for _ in range(24):
        x = torch.rand(4, 25, generator=generator)
        x[:, -1] = torch.rand(4, generator=generator)
        dynamic.append(x)
    dynamic_no_energy = [x.clone().index_fill(1, torch.tensor([24]), 0.5) for x in dynamic]
    energy = rollout(mod, dynamic)
    energy_hi = rollout(mod, dynamic_no_energy)
    dyn_main = rollout(mod, dynamic)
    dyn_abl = rollout(ablation, dynamic)
    visual_a = rollout(mod, [stream(0.5, bright=False)] * 4)
    visual_b = rollout(mod, [stream(0.5, bright=False, flip=True)] * 4)
    return {
        "main_last": main[-1].tolist(),
        "ablation_rmse": float(torch.sqrt(torch.mean((main - abl) ** 2))),
        "energy_flip_rmse": float(torch.sqrt(torch.mean((energy - energy_hi) ** 2))),
        "visual_flip_rmse": float(torch.sqrt(torch.mean((visual_a - visual_b) ** 2))),
        "dynamic_ablation_rmse": float(torch.sqrt(torch.mean((dyn_main - dyn_abl) ** 2))),
        "units_rmse": float(torch.sqrt(torch.mean((rollout(mod, xs, 302) - rollout(mod, xs, 100000)) ** 2))),
        "structure_302": brain(mod, n_units=302).structure(),
        "structure_100000": brain(mod, n_units=100000).structure(),
    }


def source_flags(name):
    text = (ROOT / "candidates" / name / "principle_organism.py").read_text()
    needles = ["eye[:, 4:]", "green[:, 0:4:2]", "age", "1.25", "0.22", "0.24", "0.42"]
    return {needle: (needle in text) for needle in needles}


if __name__ == "__main__":
    pairs = [
        ("dynamics_volatility_budget", "dynamics_volatility_budget_ablation"),
        ("agency_reafferent_turn", "agency_reafferent_turn_ablation"),
    ]
    out = {}
    for main_name, ablation_name in pairs:
        out[main_name] = summary(main_name, load(main_name), load(ablation_name))
        out[main_name]["source_flags"] = source_flags(main_name)
    print(json.dumps(out, indent=2, default=str))
