"""Controlled mechanism probe; does not estimate organism-world fitness."""

import importlib.util
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[2]


def load(name, n_sensors=49):
    path = ROOT / "candidates" / name / "principle_organism.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.OrganismBrain(302, n_sensors, 3, 1, "cpu")


def run(brain, fluctuating):
    x = torch.zeros(1, 49)
    x[0, 0:24:3] = 0.2
    values, volatilities, actions = [], [], []
    for step in range(1200):
        # Alternate the visible context; the first four pixels are context cues.
        x.zero_()
        x[0, 1] = 0.8 if (step // 100) % 2 == 0 else 0.1
        x[0, 4] = 0.1 if (step // 100) % 2 == 0 else 0.8
        x[0, 24:48:3] = 0.1
        if step % 200 < 100:
            x[0, 24] = 0.8
        else:
            x[0, 27] = 0.8
        if fluctuating and 400 <= step < 700:
            x[0, 48] = 0.2 if step % 2 == 0 else 0.8
        else:
            x[0, 48] = 0.6
        actions.append(brain.act(x).clone())
        values.append(brain.eligibility.clone())
        volatilities.append(brain.volatility.clone())
    return torch.stack(values), torch.stack(volatilities), torch.stack(actions)


def run_no_interoception(brain, steps=600):
    """With 48 sensors, coupling must be unobservable and therefore exact."""
    generator = torch.Generator().manual_seed(7331)
    traces, actions = [], []
    for _ in range(steps):
        x = torch.rand(1, 48, generator=generator)
        actions.append(brain.act(x).clone())
        traces.append(brain.eligibility.clone())
    return torch.stack(traces), torch.stack(actions)


if __name__ == "__main__":
    main = load("dynamics_energy_volatility")
    ablation = load("dynamics_energy_volatility_ablation")
    stable, _, _ = run(load("dynamics_energy_volatility"), False)
    volatile, volatility, volatile_actions = run(main, True)
    fixed, _, fixed_actions = run(ablation, True)
    no_energy, no_energy_actions = run_no_interoception(load("dynamics_energy_volatility", 48))
    no_energy_ablation, no_energy_ablation_actions = run_no_interoception(
        load("dynamics_energy_volatility_ablation", 48))
    window = slice(400, 700)
    print(json.dumps({
        "volatility_during_probe": float(volatility[window].mean()),
        "trace_mass_stable": float(stable[window].mean()),
        "trace_mass_volatile": float(volatile[window].mean()),
        "trace_mass_ablation": float(fixed[window].mean()),
        "volatile_vs_ablation_rmse": float((volatile[window] - fixed[window]).square().mean().sqrt()),
        "volatile_action_mae": float((volatile_actions - fixed_actions).abs().mean()),
        "volatile_action_changed_fraction": float((volatile_actions - fixed_actions).abs().amax(dim=2).gt(1e-6).float().mean()),
        "no_intero_trace_max_abs_diff": float((no_energy - no_energy_ablation).abs().max()),
        "no_intero_action_max_abs_diff": float((no_energy_actions - no_energy_ablation_actions).abs().max()),
        "interpretation": "mechanism probe only; not organism-world evidence",
    }, sort_keys=True))
