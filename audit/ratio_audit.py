"""Small static/runtime audit of the newest life_metabolic_ratio candidate.

This is not a judge run. It records only reproducible contract and mechanism
checks that are useful when interpreting the full result.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
from pathlib import Path

import torch


ROOT = Path(__file__).parents[1]
SRC = ROOT / "candidates/life_metabolic_ratio/principle_organism.py"


def load(path: Path):
    spec = importlib.util.spec_from_file_location("ratio_audit_candidate", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    source = SRC.read_bytes()
    tree = ast.parse(source)
    constants = sorted({node.value for node in ast.walk(tree)
                        if isinstance(node, ast.Constant)
                        and isinstance(node.value, (int, float, str))},
                       key=repr)
    text = source.decode("utf-8")
    module = load(SRC)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # 16 RGB sectors plus one interoceptive value, matching the organism API.
    a = module.OrganismBrain(302, 49, 3, 1, device, seed=7)
    b = module.OrganismBrain(100000, 49, 3, 1, device, seed=7)
    sensors = torch.zeros((1, 49), device=device)
    sensors[0, 48] = 0.95
    first_a = a.act(sensors).detach().cpu()
    first_b = b.act(sensors).detach().cpu()
    same_size_action = bool(torch.equal(first_a, first_b))
    # With no visible target, the controller still emits a deterministic
    # phase sweep; inspect the first six turn values and bite pulse positions.
    no_target = torch.zeros((1, 49), device=device)
    no_target[0, 48] = 0.95
    c = module.OrganismBrain(302, 49, 3, 1, device, seed=7)
    turns, bites = [], []
    for _ in range(12):
        out = c.act(no_target).detach().cpu()[0]
        turns.append(round(float(out[0]), 6))
        bites.append(int(out[2]))
    print({
        "sha256": hashlib.sha256(source).hexdigest(),
        "device": device,
        "fixed_rgb_table": "torch.zeros(batch, 3, 2" in text,
        "preference_shape": list(a.preference.shape),
        "fixed_visual_offset": "eye[:, 4:]" in text,
        "fixed_bite_period": "age.remainder(5) < 1" in text,
        "n_units_302_vs_100000_same_action": same_size_action,
        "structure_302": a.structure(),
        "structure_100000": b.structure(),
        "no_target_turns_first12": turns,
        "no_target_bite_first12": bites,
        "literal_constants": constants,
    })


if __name__ == "__main__":
    main()
