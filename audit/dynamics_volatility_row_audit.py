"""Causal decomposition probe for leaderboard row 182."""

import importlib.util
import json
from pathlib import Path
import types

import torch


ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = ROOT / "candidates/dynamics_volatility_budget/principle_organism.py"
ABLATION_PATH = ROOT / "candidates/dynamics_volatility_budget_ablation/principle_organism.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def module_with_budget_off():
    source = MAIN_PATH.read_text()
    original = 'budget = self.params["capacity"] * (1.0 - self.volatility).clamp_min(0.0)'
    replacement = 'budget = torch.full_like(self.volatility, self.params["capacity"])'
    if source.count(original) != 1:
        raise RuntimeError("candidate budget expression changed; review this probe")
    module = types.ModuleType("volatility_budget_off")
    exec(compile(source.replace(original, replacement), str(MAIN_PATH), "exec"), module.__dict__)
    return module


def module_with_volatility_off():
    source = MAIN_PATH.read_text()
    original = 'self.volatility.lerp_(delta.abs(), float(self.params["volatility_smoothing"]))'
    replacement = 'self.volatility.zero_()'
    if source.count(original) != 1:
        raise RuntimeError("candidate volatility update changed; review this probe")
    module = types.ModuleType("volatility_off")
    exec(compile(source.replace(original, replacement), str(MAIN_PATH), "exec"), module.__dict__)
    return module


def rollout(module, stream):
    brain = module.OrganismBrain(302, 49, 3, 16, "cpu", seed=19)
    actions = []
    states = []
    for sensors in stream:
        actions.append(brain.act(sensors).detach().clone())
        states.append({
            "volatility": brain.volatility.detach().clone(),
            "trace_mass": brain.eligibility.sum(dim=(1, 2)).detach().clone(),
            "preference_norm": brain.preference.flatten(1).norm(dim=1).detach().clone(),
        })
    return torch.stack(actions), states


def rmse(left, right):
    return float(torch.sqrt(torch.mean((left - right) ** 2)))


def main():
    main_module = load(MAIN_PATH, "volatility_main")
    ablation_module = load(ABLATION_PATH, "volatility_ablation")
    budget_off = module_with_budget_off()
    volatility_off = module_with_volatility_off()

    generator = torch.Generator().manual_seed(20261025)
    dynamic = []
    stable = []
    for step in range(48):
        x = torch.rand((16, 49), generator=generator)
        x[:, -1] = 0.95 if step < 8 else (0.58 if step % 4 < 2 else 0.82)
        dynamic.append(x)
        y = x.clone()
        y[:, -1] = 0.95
        stable.append(y)

    modules = {
        "main": main_module,
        "published_ablation_trace_coupling_off": ablation_module,
        "budget_compression_off": budget_off,
        "all_volatility_modulation_off": volatility_off,
    }
    dynamic_runs = {name: rollout(module, dynamic) for name, module in modules.items()}
    stable_runs = {name: rollout(module, stable) for name, module in modules.items()}

    out = {
        "scope": "deterministic implementation probe only; not organism-world evidence",
        "steps": len(dynamic),
        "batch": 16,
        "sensor_width": 49,
        "dynamic_energy_values": [0.95, 0.58, 0.82],
        "dynamic_action_rmse_vs_main": {
            name: rmse(dynamic_runs["main"][0], run[0])
            for name, run in dynamic_runs.items() if name != "main"
        },
        "stable_energy_action_rmse_vs_main": {
            name: rmse(stable_runs["main"][0], run[0])
            for name, run in stable_runs.items() if name != "main"
        },
        "final_mean_state": {
            name: {key: float(value.mean()) for key, value in run[1][-1].items()}
            for name, run in dynamic_runs.items()
        },
        "ablation_budget_expression": "budget=capacity*(1-volatility); remains active when volatility_coupling=0",
        "candidate_hash": __import__("hashlib").sha256(MAIN_PATH.read_bytes()).hexdigest(),
        "ablation_hash": __import__("hashlib").sha256(ABLATION_PATH.read_bytes()).hexdigest(),
    }
    result_path = Path(__file__).with_suffix(".result.json")
    result_path.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
