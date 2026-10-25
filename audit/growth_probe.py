"""Small synthetic audit of growth_local_eligibility invariants."""

import importlib.util
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "candidates/growth_local_eligibility/principle_organism.py"
spec = importlib.util.spec_from_file_location("growth_candidate", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def make_brain(units, params=None):
    return module.OrganismBrain(units, 49, 3, 4, "cpu", seed=9, params=params)


generator = torch.Generator().manual_seed(19)
sensors = torch.rand((24, 4, 49), generator=generator)
sensors[:, :, -1] = torch.linspace(0.05, 0.95, 24)[:, None].expand(-1, 4)


def replay(brain, transform=lambda x: x):
    outputs = []
    for frame in sensors:
        outputs.append(brain.act(transform(frame)))
    return torch.stack(outputs)


small = make_brain(302)
large = make_brain(100000)
small_actions = replay(small)
large_actions = replay(large)
no_learning_actions = replay(make_brain(302, {"association_gain": 0.0}))
permuted_actions = replay(
    make_brain(302),
    lambda x: torch.cat((x[:, 1:2], x[:, 0:1], x[:, 2:3], x[:, 3:]), dim=1),
)

result = {
    "source_sha256": __import__("hashlib").sha256(SOURCE.read_bytes()).hexdigest(),
    "max_action_delta_units_302_vs_100000": float((small_actions - large_actions).abs().max()),
    "max_action_delta_gain_0_vs_base": float((small_actions - no_learning_actions).abs().max()),
    "max_action_delta_red_green_swap": float((small_actions - permuted_actions).abs().max()),
    "structure_302": small.structure(),
    "structure_100000": large.structure(),
    "trace_bytes_batch": small.trace.numel() * small.trace.element_size(),
    "trace_bytes_batch_at_100000": large.trace.numel() * large.trace.element_size(),
    "key_index_bytes_shared": small.key_index.numel() * small.key_index.element_size(),
    "reported_memory_bytes_batch": small.structure()["memory_bytes"],
    "persistent_tensor_bytes_batch": sum(
        tensor.numel() * tensor.element_size()
        for tensor in [small.trace, small.key_index, small.previous_pixel,
                       small.previous_color, small.previous_value,
                       small.previous_energy, small.previous_bite, small.angles]
    ),
}
print(json.dumps(result, sort_keys=True))
