"""Evaluate the H017 energy-delta predictor on held-out signal regimes."""

import importlib.util
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[2]


def load_brain():
    path = ROOT / "candidates" / "dynamics_surprise_retention" / "principle_organism.py"
    spec = importlib.util.spec_from_file_location("surprise_forecast", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.OrganismBrain


def run_regime(brain_cls, energies):
    batch = energies.shape[0]
    brain = brain_cls(302, 49, 3, batch, "cpu")
    eye = torch.zeros(batch, 48)
    predictions, actuals = [], []
    previous = None
    for energy in energies.unbind(1):
        sensors = torch.cat((eye, energy[:, None]), dim=1)
        prediction = brain.predicted_delta.clone()
        if previous is not None:
            actual = (energy - previous).clamp(-0.2, 0.2)
            predictions.append(prediction)
            actuals.append(actual)
        brain.act(sensors)
        previous = energy
    prediction = torch.stack(predictions, dim=1)
    actual = torch.stack(actuals, dim=1)
    return (prediction - actual).abs().mean().item(), actual.abs().mean().item()


def main():
    torch.manual_seed(17)
    cls = load_brain()
    batch, steps = 64, 1200
    t = torch.arange(steps, dtype=torch.float32)[None, :]
    phase = torch.linspace(0, 2 * torch.pi, batch + 1)[:-1, None]

    smooth = (0.5 + 0.18 * torch.sin(2 * torch.pi * t / 240 + phase)).clamp(0, 1)
    shock = smooth.clone()
    shock[:, 500:650] += 0.14
    shock.clamp_(0, 1)
    noise = 0.2 + 0.6 * torch.rand(batch, steps)
    for name, sequence in (("smooth", smooth), ("shock", shock), ("noise", noise)):
        predictor_mae, mean_delta = run_regime(cls, sequence)
        zero_mae = mean_delta
        gain = zero_mae - predictor_mae
        print(f"{name}: predictor_mae={predictor_mae:.6f} zero_mae={zero_mae:.6f} "
              f"gain={gain:.6f}")


if __name__ == "__main__":
    main()
