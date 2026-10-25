"""Diagnostic audit of H005's projected Hebbian update.

This is not a judge score. It measures the exact norm projection invariant,
weight movement, and whether n_units participates.
"""
import importlib.util
import json
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "candidates/axiom_capacity_correlation/principle.py"


def load():
    spec = importlib.util.spec_from_file_location("h005_projection", SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(mod, n_units, stream):
    brain = mod.OrganismBrain(n_units, stream.shape[1], 3, 1, "cpu", seed=23)
    initial = brain.weights.detach().clone()
    row_norms = []
    actions = []
    for x in stream:
        actions.append(brain.act(x[None, :]).detach().clone())
        row_norms.append(brain.weights.norm(dim=2).detach().clone())
    return brain, initial, torch.cat(actions), torch.stack(row_norms)


def main():
    torch.manual_seed(4)
    stream = torch.rand(240, 49)
    mod = load()
    small, initial, actions_small, norms = run(mod, 302, stream)
    large, _, actions_large, _ = run(mod, 100000, stream)

    initial_rows = initial.norm(dim=2)
    norm_error = (norms - initial_rows[None, :, :]).abs()
    weight_delta = (small.weights - initial).norm().item()

    result = {
        "source": str(SRC.relative_to(ROOT)),
        "prior_art": "Oja projected/local Hebbian normalization; arXiv:2408.08408 fetched via shared/lit.py",
        "steps": int(stream.shape[0]),
        "max_row_norm_error": float(norm_error.max()),
        "mean_row_norm_error": float(norm_error.mean()),
        "final_weight_frobenius_delta": weight_delta,
        "n_units_action_max_abs_delta": float((actions_small - actions_large).abs().max()),
        "structure_302": small.structure(),
        "structure_100000": large.structure(),
        "n_units_ignored_by_constructor": bool(small.width == large.width),
    }
    out = ROOT / "audit/h005_projection_audit.result.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
