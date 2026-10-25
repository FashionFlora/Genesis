"""Focused critic probe for the two newest capacity-correlation rows."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "axiom_global_capacity_covariance": ROOT / "candidates/axiom_global_capacity_covariance/principle.py",
    "axiom_centered_correlation": ROOT / "candidates/axiom_centered_correlation/principle.py",
}


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.OrganismBrain


def run(brain_cls, n_units: int, seed: int = 7):
    torch.manual_seed(seed)
    b, s, m, t = 8, 12, 3, 240
    brain = brain_cls(n_units, s, m, b, "cpu", seed=seed)
    g = torch.Generator().manual_seed(91)
    stream = torch.rand(t, b, s, generator=g)
    before = brain.act(stream[0]).detach().clone()
    actions = [before]
    for x in stream[1:]:
        actions.append(brain.act(x).detach().clone())
    actions = torch.stack(actions)
    fresh = brain_cls(n_units, s, m, b, "cpu", seed=seed)
    frozen_steps = []
    for x in stream:
        # Keep the source's state bookkeeping, but suppress the coactivity
        # update so this is a matched frozen-weight trajectory.
        fresh.trace.zero_()
        fresh.previous_sensor_delta.zero_()
        fresh.previous_action_delta.zero_()
        fresh.has_previous.zero_()
        frozen_steps.append(fresh.act(x).detach())
    frozen = torch.stack(frozen_steps)
    perm = torch.arange(s - 1, -1, -1)
    perm_brain = brain_cls(n_units, s, m, b, "cpu", seed=seed)
    permuted = torch.stack([perm_brain.act(x[:, perm]).detach() for x in stream])
    return {
        "n_units": n_units,
        "structure": brain.structure(),
        "learned_vs_frozen_rmse": float((actions - frozen).square().mean().sqrt()),
        "n_units_repeat_rmse": None,
        "permutation_rmse": float((actions - permuted).square().mean().sqrt()),
        "action_abs_mean": float(actions.abs().mean()),
        "weight_norm": float(brain.weights.norm().item()),
        "_actions": actions,
    }


def main():
    out = {}
    for name, path in TARGETS.items():
        cls = load(path, name)
        small = run(cls, 302)
        large = run(cls, 100000)
        units_rmse = float((small["_actions"] - large["_actions"]).square().mean().sqrt())
        small["n_units_repeat_rmse"] = units_rmse
        large["n_units_repeat_rmse"] = units_rmse
        small.pop("_actions")
        large.pop("_actions")
        out[name] = {
            "principle_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "adapter_sha256": hashlib.sha256(
                (path.parent / "principle_organism.py").read_bytes()
            ).hexdigest(),
            "small": small,
            "large": large,
            "source_flags": {
                "global_sensor_count_shape": "n_sensors" in path.read_text(),
                "hardcoded_rgb_or_world_terms": any(
                    token in path.read_text().lower()
                    for token in ("rgb", "color", "energy", "room", "food", "reward")
                ),
            },
        }
    (ROOT / "audit/new_rows_probe.result.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
