"""Matched implementation probe for the two metabolic-retention candidates."""

import importlib.util
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "dynamics_metabolic_retention": ROOT / "candidates/dynamics_metabolic_retention/principle_organism.py",
    "axiom_metabolic_retention_budget": ROOT / "candidates/axiom_metabolic_retention_budget/principle_organism.py",
}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(module, sensors, n_units=302, params=None):
    brain = module.OrganismBrain(n_units, sensors.shape[-1], 3, sensors.shape[0], "cpu", seed=19, params=params)
    actions = []
    for frame in sensors.unbind(1):
        actions.append(brain.act(frame).clone())
    return torch.stack(actions, 1), brain.structure()


def main():
    torch.manual_seed(20261025)
    batch, steps, eye_width = 96, 80, 16
    eyes = torch.rand(batch, steps, eye_width * 3)
    energy = torch.rand(batch, steps, 1)
    energy[:, :20] = 0.9
    energy[:, 20:40] = 0.15
    energy[:, 40:60] = 0.9
    energy[:, 60:] = 0.15
    sensors = torch.cat((eyes, energy), dim=-1)
    result = {"seed": 20261025, "batch": batch, "steps": steps, "sources": {}}

    for name, path in SOURCES.items():
        module = load(path, name)
        actions, structure = run(module, sensors)
        control, _ = run(module, sensors, params={"energy_coupling": 0.0})
        large, structure_large = run(module, sensors, n_units=100000)
        bright = torch.zeros(1, 12, eye_width * 3 + 1)
        bright[:, :, 4 * 3 + 1] = 0.8
        bright[:, :, -1] = 0.8
        bright_actions, _ = run(module, bright)
        result["sources"][name] = {
            "source_sha256": __import__("hashlib").sha256(path.read_bytes()).hexdigest(),
            "coupling_off_action_rmse": float((actions - control).square().mean().sqrt()),
            "coupling_off_action_max": float((actions - control).abs().max()),
            "n_units_action_max_delta": float((actions - large).abs().max()),
            "structure_302": structure,
            "structure_100000": structure_large,
            "fixed_bright_bite_ages": torch.where(bright_actions[0, :, 2] > 0)[0].tolist(),
            "state_tensor_cells_per_organism": sum(
                int(v.numel() // batch)
                for v in vars(module.OrganismBrain(302, 49, 3, batch, "cpu", seed=19)).values()
                if isinstance(v, torch.Tensor) and v.ndim > 0 and v.shape[0] == batch
            ),
        }

    out = ROOT / "audit/tournament_retention_pair.result.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
