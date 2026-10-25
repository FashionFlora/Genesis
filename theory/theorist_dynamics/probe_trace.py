"""Controlled CPU probe of energy-trace learning; not an organism judge."""

import importlib.util
from pathlib import Path
import statistics

import torch


ROOT = Path(__file__).resolve().parents[2]
N = 64


def load_brain(name):
    path = ROOT / "candidates" / name / "principle_organism.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.OrganismBrain


def sensor_contract(Brain):
    brain = Brain(302, 48, 3, 1, "cpu")
    first = torch.zeros(1, 48)
    brain.act(first)
    first[0, -1] = 1
    brain.act(first)
    assert brain.eye_width == 16 and brain.energy_index is None
    assert torch.count_nonzero(brain.preference) == 0
    with_energy = Brain(302, 49, 3, 1, "cpu")
    assert with_energy.eye_width == 16 and with_energy.energy_index == 48


def run(Brain, learning_rate, seed, shuffled=False):
    brain = Brain(302, 49, 3, N, "cpu", params={"learning_rate": learning_rate})
    generator = torch.Generator().manual_seed(seed)
    assignment = (torch.randperm(N, generator=generator) >= N // 2).long()
    shuffle_order = torch.randperm(N, generator=generator)
    # Each world's good color is opposite in the two contexts.
    optimum = torch.stack((assignment, 1 - assignment), dim=1)
    energy = torch.full((N,), 0.5)
    pending = torch.zeros(N)
    correct = {"A_train": [], "B_switch": [], "B_late": [], "A_return": [], "A_late": []}
    steps = [(0, "A_train", 500), (1, "B_switch", 500), (0, "A_return", 500)]
    for context, label, count in steps:
        for t in range(count):
            prior_context = brain.previous_context
            payoff = (brain.previous_color == optimum[torch.arange(N), prior_context]).float()
            payoff = payoff * 0.02 - 0.01
            pending = payoff[shuffle_order] if shuffled else payoff
            energy = 0.5 + 0.9 * (energy - 0.5) + pending
            energy.clamp_(0.05, 0.95)

            x = torch.zeros(N, 49)
            eye = x[:, :48].reshape(N, 16, 3)
            if context == 0:
                eye[:, 0, 1] = eye[:, 2, 1] = 0.4
            else:
                eye[:, 1, 1] = eye[:, 3, 1] = 0.4
            eye[:, 4:] = 0.2
            x[:, 48] = energy
            brain.act(x)
            chosen = brain.previous_color
            score = (chosen == optimum[:, context]).float().mean().item()
            if (label == "A_train" and t >= 400) or (label == "B_switch" and t < 100):
                correct[label].append(score)
            if (label == "B_switch" and t >= 400) or (label == "A_return" and t < 100) or (label == "A_return" and t >= 400):
                key = "B_late" if label == "B_switch" else ("A_return" if t < 100 else "A_late")
                correct[key].append(score)
    return {key: round(sum(vals) / len(vals), 4) for key, vals in correct.items()}


def main():
    torch.set_num_threads(1)
    Brain = load_brain("dynamics_energy_trace")
    Ablation = load_brain("dynamics_energy_trace_ablation")
    sensor_contract(Brain)
    print("sensor_contract=pass (48 RGB, 49 RGB+energy)")
    conditions = (
        ("trace", Brain, 0.35, False),
        ("credit_off", Ablation, 0.0, False),
        ("shuffled_energy", Brain, 0.35, True),
    )
    for label, cls, lr, shuffled in conditions:
        trials = [run(cls, lr, seed, shuffled) for seed in range(8)]
        means = {
            key: round(statistics.mean(trial[key] for trial in trials), 4)
            for key in trials[0]
        }
        sds = {
            key: round(statistics.stdev(trial[key] for trial in trials), 4)
            for key in trials[0]
        }
        print(f"{label}: mean={means}, seed_sd={sds}, seeds=8, worlds/seed={N}")


if __name__ == "__main__":
    main()
