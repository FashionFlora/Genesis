"""Small deterministic probes for candidate policy leakage and scaling."""
import importlib.util
import json
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "dynamics_metabolic_contrast": "candidates/dynamics_metabolic_contrast/principle_organism.py",
    "axiom_metabolic_retention_budget": "candidates/axiom_metabolic_retention_budget/principle_organism.py",
    "agency_sensorimotor_prediction": "candidates/agency_sensorimotor_prediction/principle_organism.py",
}


def jsonable(value):
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return float(value.item())
        return {"shape": list(value.shape), "mean": float(value.float().mean())}
    if isinstance(value, dict):
        return {key: jsonable(item) for key, item in value.items()}
    return value


def load(rel, suffix=""):
    spec = importlib.util.spec_from_file_location(rel.replace("/", "_") + suffix, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rollout(mod, x, units=302, seed=7):
    batch = x.shape[1] if x.ndim == 3 else x.shape[0]
    sensors = x.shape[-1]
    brain = mod.OrganismBrain(units, sensors, 3, batch, "cpu", seed=seed)
    out = []
    if x.ndim == 3:
        for frame in x:
            out.append(brain.act(frame).detach().clone())
    else:
        out.append(brain.act(x).detach().clone())
    return torch.stack(out), brain.structure()


def main():
    torch.manual_seed(19)
    batch, width = 8, 16
    base = torch.rand(batch, width, 3)
    energy = torch.rand(batch, 1)
    x = torch.cat((base.reshape(batch, -1), energy), dim=1)
    # A fixed bright source makes any time gate visible without world dynamics.
    fixed = torch.zeros(12, batch, width, 3)
    fixed[:, :, 8, 1] = 1.0
    fixed = torch.cat((fixed.reshape(12, batch, -1), torch.full((12, batch, 1), 0.5)), dim=2)
    result = {}
    for name, path in TARGETS.items():
        mod = load(path)
        a302, s302 = rollout(mod, x, 302)
        a100k, s100k = rollout(mod, x, 100000)
        fixed_actions, _ = rollout(mod, fixed, 302)
        # Swap red and green in every pixel while preserving geometry and energy.
        swapped = base[:, :, [1, 0, 2]].reshape(batch, -1)
        swapped = torch.cat((swapped, energy), dim=1)
        swap_actions, _ = rollout(mod, swapped, 302)
        result[name] = {
            "capacity_max_action_delta": float((a302 - a100k).abs().max()),
            "structure_302": jsonable(s302),
            "structure_100000": jsonable(s100k),
            "red_green_swap_max_action_delta": float((a302 - swap_actions).abs().max()),
            "fixed_source_bite_ages": fixed_actions[:, 0, 2].nonzero().flatten().tolist(),
            "fixed_source_bite_count": int(fixed_actions[:, :, 2].sum()),
        }
    out = json.dumps(result, indent=2, sort_keys=True)
    print(out)
    (ROOT / "audit/current_candidates_probe.result.json").write_text(out + "\n")


if __name__ == "__main__":
    main()
