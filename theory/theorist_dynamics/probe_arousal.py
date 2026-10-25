"""Small deterministic probe for metabolic arousal, not an organism score."""

import importlib.util
import statistics
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[2]


def load(name):
    path = ROOT / "candidates" / name / "principle_organism.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.OrganismBrain


def run(Brain, energy, steps=240):
    brain = Brain(302, 49, 3, 1, "cpu", seed=11)
    output = []
    for _ in range(steps):
        sensors = torch.zeros(1, 49)
        sensors[0, 8 * 3 + 1] = 0.30
        sensors[0, -1] = energy
        output.append(brain.act(sensors)[0])
    action = torch.stack(output)
    return {
        "late_drive": round(float(action[-40:, 1].mean()), 6),
        "late_bite": round(float(action[-40:, 2].mean()), 6),
        "arousal": round(float(brain.arousal[0]), 6),
    }


def main():
    torch.set_num_threads(1)
    for name in ("dynamics_metabolic_arousal", "dynamics_metabolic_arousal_ablation"):
        Brain = load(name)
        print(name, "low", run(Brain, 0.10))
        print(name, "high", run(Brain, 0.90))
        hidden = Brain(302, 48, 3, 1, "cpu", seed=11)
        sensors = torch.zeros(1, 48)
        actions = torch.stack([hidden.act(sensors)[0] for _ in range(40)])
        print(name, "hidden", {"finite": bool(torch.isfinite(actions).all()),
                                "arousal": round(float(hidden.arousal[0]), 6)})


if __name__ == "__main__":
    main()
