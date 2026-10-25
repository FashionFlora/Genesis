"""Small mechanism probe for predictive energy-surprise retention."""

import importlib.util
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    path = ROOT / "candidates" / name / "principle_organism.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.OrganismBrain


def run(cls, sequence, n_sensors=49):
    batch = 32
    brain = cls(302, n_sensors, 3, batch, "cpu")
    masses = []
    actions = []
    for energy in sequence:
        eye = torch.rand(batch, 48)
        eye[:, 0] = 0.7
        eye[:, 6] = 0.4
        x = torch.cat((eye, torch.full((batch, 1), energy)), dim=1)
        actions.append(brain.act(x).detach())
        masses.append(float(brain.eligibility.sum(1).mean()))
    return torch.stack(actions), masses, brain


def main():
    main_cls = load("dynamics_surprise_retention")
    off_cls = load("dynamics_surprise_retention_ablation")
    stable = [0.5 for _ in range(120)]
    reversal = [0.5 for _ in range(58)] + [0.9, 0.1] + [0.5 for _ in range(60)]
    a_stable, m_stable, _ = run(main_cls, stable)
    a_reversal, m_reversal, _ = run(main_cls, reversal)
    a_off, m_off, _ = run(off_cls, reversal)
    _, _, no_intero = run(main_cls, stable, n_sensors=48)
    print(f"stable_mass_last={m_stable[-1]:.6f}")
    print(f"reversal_mass_before={m_reversal[59]:.6f} after={m_reversal[-1]:.6f}")
    print(f"ablation_mass_after={m_off[-1]:.6f}")
    print(f"reversal_main_ablation_action_mae={(a_reversal-a_off).abs().mean().item():.6f}")
    print(f"no_intero_energy_state={float(no_intero.predicted_delta.abs().max()):.6f}")
    print(f"stable_vs_reversal_action_mae={(a_stable-a_reversal).abs().mean().item():.6f}")


if __name__ == "__main__":
    main()
