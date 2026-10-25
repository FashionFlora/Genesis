"""Audit row 174: sparse claim, metabolic factor, and capacity invariance."""

import hashlib
import importlib.util
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tensor_bytes(brain):
    return int(sum(v.numel() * v.element_size() for v in vars(brain).values()
                   if isinstance(v, torch.Tensor)))


def run(mod, stream, units=302, batch=None, params=None):
    batch = batch or stream.shape[1]
    brain = mod.OrganismBrain(units, stream.shape[2], 3, batch, "cpu", seed=7,
                              params=params)
    actions = []
    for t in range(stream.shape[0]):
        actions.append(brain.act(stream[t]).detach().clone())
    return torch.stack(actions), brain, tensor_bytes(brain)


def make_metabolic_control(path):
    """Load an isolated copy with only reserve weighting removed."""
    source = (ROOT / path).read_text(encoding="utf-8")
    old = "self.previous_value * outcome * self.previous_energy"
    assert source.count(old) == 1
    source = source.replace(old, "self.previous_value * outcome")
    namespace = {"__name__": "growth_metabolic_sparse_control"}
    exec(compile(source, str(ROOT / path), "exec"), namespace)
    class Module:
        OrganismBrain = namespace["OrganismBrain"]
    return Module


def main():
    candidate_path = "candidates/growth_metabolic_sparse/principle_organism.py"
    parent_path = "candidates/growth_local_eligibility/principle_organism.py"
    cand = load(candidate_path, "growth_metabolic_sparse_audit")
    parent = load(parent_path, "growth_local_eligibility_audit")
    control = make_metabolic_control(candidate_path)

    torch.manual_seed(19)
    # Deliberately varied eyes and energy make delayed credit observable.
    stream = torch.rand(96, 4, 49)
    stream[:, :, -1] = torch.rand(96, 4)
    actions, brain, actual_bytes = run(cand, stream)
    frozen_actions, frozen_brain, frozen_bytes = run(control, stream)
    parent_actions, parent_brain, parent_bytes = run(parent, stream)

    # Independent-batch check: row 0 must match a separately instantiated brain.
    row0, _, _ = run(cand, stream[:, :1], batch=1)
    batch_delta = float((actions[:, :1] - row0).abs().max())

    cap_actions, cap_brain, cap_bytes = run(cand, stream, units=100000)
    fresh = cand.OrganismBrain(302, 49, 3, 4, "cpu", seed=7)
    fresh_report = fresh.structure()
    fresh_bytes = tensor_bytes(fresh)
    out = {
        "candidate": "growth_metabolic_sparse",
        "source_sha256": hashlib.sha256((ROOT / candidate_path).read_bytes()).hexdigest(),
        "parent_source_sha256": hashlib.sha256((ROOT / parent_path).read_bytes()).hexdigest(),
        "stream_shape": list(stream.shape),
        "reserve_vs_no_reserve_action_rmse": float((actions - frozen_actions).pow(2).mean().sqrt()),
        "reserve_vs_no_reserve_action_max": float((actions - frozen_actions).abs().max()),
        "candidate_vs_parent_action_rmse": float((actions - parent_actions).pow(2).mean().sqrt()),
        "candidate_vs_parent_action_max": float((actions - parent_actions).abs().max()),
        "capacity_action_rmse_302_vs_100000": float((actions - cap_actions).pow(2).mean().sqrt()),
        "capacity_action_max_302_vs_100000": float((actions - cap_actions).abs().max()),
        "batch_independence_max": batch_delta,
        "reported_structure": brain.structure(),
        "reported_structure_fresh": fresh_report,
        "reported_structure_control": frozen_brain.structure(),
        "reported_structure_parent": parent_brain.structure(),
        "reported_structure_100000": cap_brain.structure(),
        "actual_tensor_bytes_candidate": actual_bytes,
        "actual_tensor_bytes_fresh": fresh_bytes,
        "actual_tensor_bytes_no_reserve": frozen_bytes,
        "actual_tensor_bytes_parent": parent_bytes,
        "actual_tensor_bytes_100000": cap_bytes,
        "source_note": "candidate stores trace/active/key_index densely for every pixel-color slot",
    }
    out_path = Path(__file__).with_suffix(".result.json")
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
