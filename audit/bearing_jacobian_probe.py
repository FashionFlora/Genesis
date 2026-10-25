"""Probe the isolated action effect and sensor dependencies of bearing credit."""

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


def rollout(module, observations, n_units=302):
    brain = module.OrganismBrain(n_units, 49, 3, 4, "cpu", seed=17)
    return torch.stack([brain.act(x) for x in observations])


def eye(pixel, amount=0.8, energy=0.5):
    x = torch.zeros(4, 49)
    x[:, pixel * 3:pixel * 3 + 3] = amount / 3
    x[:, -1] = energy
    return x


def rmse(a, b):
    return float(torch.sqrt(torch.mean((a - b) ** 2)))


def main():
    main = load("agency_bearing_jacobian")
    ablation = load("agency_bearing_jacobian_ablation")
    stream = [eye(pixel, amount) for pixel, amount in
              [(4, 0.8), (4, 1.8), (12, 0.2), (12, 1.8), (7, 1.0)] * 8]
    changed_energy = [x.clone() for x in stream]
    for x in changed_energy:
        x[:, -1] = 0.99 - x[:, -1]
    dark = [torch.zeros(4, 49) for _ in range(20)]
    result = {
        "steps": len(stream),
        "main_ablation_rmse": rmse(rollout(main, stream), rollout(ablation, stream)),
        "main_energy_flip_rmse": rmse(rollout(main, stream), rollout(main, changed_energy)),
        "dark_main_ablation_rmse": rmse(rollout(main, dark), rollout(ablation, dark)),
        "n_units_302_100000_rmse": rmse(rollout(main, stream, 302), rollout(main, stream, 100000)),
        "structure_302": main.OrganismBrain(302, 49, 3, 4, "cpu", seed=17).structure(),
        "structure_100000": main.OrganismBrain(100000, 49, 3, 4, "cpu", seed=17).structure(),
        "source_literals": {s: s in Path(main.__file__).read_text() for s in
                            ["total > 0.10", "total > 1.25", "concentration > 0.22",
                             "age * 0.037", "tanh(1.9 * bearing)", "explore_turn"]},
    }
    out = Path(__file__).with_name("bearing_jacobian_probe.result.json")
    out.write_text(json.dumps(result, indent=2, default=lambda x: x.tolist()) + "\n")
    print(json.dumps(result, indent=2, default=lambda x: x.tolist()))


if __name__ == "__main__":
    main()
