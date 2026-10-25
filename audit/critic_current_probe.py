"""Small contract/policy probes for current leader and H005.

These are implementation audits, not organism-judge scores.
"""
import importlib.util
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem + str(path), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def leader_probe():
    mod = load(ROOT / "candidates/dynamics_metabolic_retention/principle_organism.py")
    batch, sensors = 64, 49  # 16 RGB pixels plus interoception
    g = torch.Generator().manual_seed(17)
    eye = torch.rand(batch, 48, generator=g)
    energy = torch.rand(batch, 1, generator=g)
    stream = torch.cat((eye, energy), dim=1)

    def run(n_units, x):
        brain = mod.OrganismBrain(n_units, sensors, 3, 1, "cpu", seed=31)
        out = []
        for row in x:
            out.append(brain.act(row[None, :]).squeeze(0))
        return torch.stack(out)

    base = run(302, stream)
    large = run(100000, stream)
    no_energy = run(302, torch.cat((eye, torch.zeros_like(energy)), dim=1))

    # Move a bright source from sector 0 to sector 8 without changing its mass.
    scene = torch.zeros(1, sensors)
    scene[0, 0] = 0.8
    scene_shift = torch.zeros_like(scene)
    scene_shift[0, 4 * 3] = 0.8
    b = mod.OrganismBrain(302, sensors, 3, 1, "cpu", seed=0)
    bites = []
    for age in range(15):
        row = scene if age == 0 else scene
        bites.append(float(b.act(row)[0, 2]))

    return {
        "n_units_action_max_abs_delta": float((base - large).abs().max()),
        "energy_zero_action_rmse": float(torch.sqrt(((base - no_energy) ** 2).mean())),
        "energy_zero_action_changed_fraction": float((base != no_energy).any(dim=1).float().mean()),
        "retinal_layout_action_delta": float((run(302, scene.repeat(8, 1)) - run(302, scene_shift.repeat(8, 1))).abs().mean()),
        "visible_source_bite_by_age_0_to_14": bites,
        "structure_302": mod.OrganismBrain(302, sensors, 3, 1, "cpu").structure(),
        "structure_100000": mod.OrganismBrain(100000, sensors, 3, 1, "cpu").structure(),
    }


def h005_probe():
    mod = load(ROOT / "candidates/axiom_capacity_correlation/principle.py")
    brain = mod.OrganismBrain(302, 49, 3, 1, "cpu", seed=3)
    initial = brain.capacity.clone()
    g = torch.Generator().manual_seed(9)
    for _ in range(200):
        brain.act(torch.rand(1, 49, generator=g))
    row_norm = brain.weights.norm(dim=2)
    total_norm = brain.weights.norm()
    initial_total = initial.norm()
    return {
        "structure": brain.structure(),
        "row_norm_max_abs_delta": float((row_norm - initial.squeeze(-1)).abs().max()),
        "global_norm_delta": float((total_norm - initial_total).abs()),
        "capacity_shape": list(brain.capacity.shape),
        "n_units_ignored_in_code": True,
    }


if __name__ == "__main__":
    result = {"leader": leader_probe(), "h005": h005_probe()}
    out = ROOT / "audit/critic_current_probe.result.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
