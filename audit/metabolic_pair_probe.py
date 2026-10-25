"""Reproducible pairwise audit for the two current metabolic candidates."""

import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SOURCES = {
    "dynamics_metabolic_retention": ROOT / "candidates/dynamics_metabolic_retention/principle_organism.py",
    "life_metabolic_context": ROOT / "candidates/life_metabolic_context/principle_organism.py",
}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def actions(mod, sensors, n_units):
    brain = mod.OrganismBrain(n_units, sensors.shape[1], 3, sensors.shape[0], "cpu", seed=19)
    return torch.stack([brain.act(sensors) for _ in range(8)])


def energy_delta(mod, base):
    low = base.clone()
    high = base.clone()
    low[:, -1] = 0.0
    high[:, -1] = 1.0
    # Compare the same retinal stream with alternating versus absent energy
    # changes.  This reveals retention in state even when action is unchanged.
    a = mod.OrganismBrain(302, 49, 3, base.shape[0], "cpu", seed=3)
    b = mod.OrganismBrain(302, 49, 3, base.shape[0], "cpu", seed=3)
    action_a = action_b = None
    for step in range(20):
        action_a = a.act(high if step % 2 else low)
        action_b = b.act(low)
    return {
        "final_action_max_abs_delta": float((action_a - action_b).abs().max()),
        "preference_state_max_abs_delta": float((a.preference - b.preference).abs().max()),
        "eligibility_state_max_abs_delta": float((a.eligibility - b.eligibility).abs().max()),
    }


def main():
    from sandbox.worlds.organism import OrganismWorld

    world = OrganismWorld(batch=256, device="cpu", seed=19)
    sensors = world.observe()
    eye = sensors[:, :48].reshape(256, 16, 3)
    room_context = world.room_context
    decoded = (eye[:, 1::2, 1].mean(1) > eye[:, 0::2, 1].mean(1)).long()
    swapped = sensors.clone()
    swapped[:, 0:3], swapped[:, 3:6] = sensors[:, 3:6].clone(), sensors[:, 0:3].clone()
    result = {
        "seed": 19,
        "batch": 256,
        "sources": {},
        "shared_sensor_probe": {
            "room_context_accuracy_odd_even_green": float((decoded == room_context).float().mean()),
            "cue_flip_fraction_after_first_pixel_swap": float(
                (decoded != ((swapped[:, :48].reshape(256, 16, 3)[:, 1::2, 1].mean(1)
                             > swapped[:, :48].reshape(256, 16, 3)[:, 0::2, 1].mean(1)).long())).float().mean()
            ),
        },
    }
    for name, path in SOURCES.items():
        mod = load(path, name)
        a302 = actions(mod, sensors, 302)
        a100k = actions(mod, sensors, 100000)
        result["sources"][name] = {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "structure_302": mod.OrganismBrain(302, 49, 3, 256, "cpu", seed=19).structure(),
            "structure_100000": mod.OrganismBrain(100000, 49, 3, 256, "cpu", seed=19).structure(),
            "action_max_abs_diff_302_vs_100000": float((a302 - a100k).abs().max()),
            "action_max_abs_diff_after_pixel_swap": float(
                (actions(mod, sensors, 302) - actions(mod, swapped, 302)).abs().max()
            ),
            "energy_only_state_probe": energy_delta(mod, sensors),
            "static_flags": {
                "odd_even_green_context": bool(re.search(r"odd.*even|even.*odd", path.read_text(), re.S)),
                "target_offset_eye_4": "eye[:, 4:]" in path.read_text(),
                "age_mod_5_bite": "remainder(5)" in path.read_text(),
            },
        }
    out = ROOT / "audit/metabolic_pair_probe.result.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
