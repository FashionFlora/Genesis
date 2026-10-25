"""Probe fixed retinal/context choices in the life_metabolic_context leader."""

import importlib.util
import json
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SRC = ROOT / "candidates/life_metabolic_context/principle_organism.py"
spec = importlib.util.spec_from_file_location("life_context", SRC)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
from sandbox.worlds.organism import OrganismWorld


def context_bit(sensors):
    eye = sensors[:, :48].reshape(sensors.shape[0], 16, 3)
    return (eye[:, 1::2, 1].mean(1) > eye[:, 0::2, 1].mean(1)).long()


def main():
    world = OrganismWorld(batch=256, device="cpu", seed=19)
    sensors = world.observe()
    original = context_bit(sensors)
    swapped = sensors.clone()
    # Exchange two retinal positions while preserving all channel values.
    swapped[:, 0:3], swapped[:, 3:6] = sensors[:, 3:6].clone(), sensors[:, 0:3].clone()
    permuted = context_bit(swapped)

    brain = mod.OrganismBrain(302, 49, 3, 256, "cpu", seed=19)
    for _ in range(4):
        brain.act(sensors)
    action_original = brain.act(sensors)
    brain2 = mod.OrganismBrain(302, 49, 3, 256, "cpu", seed=19)
    for _ in range(4):
        brain2.act(swapped)
    action_swapped = brain2.act(swapped)

    # Bright isolated target makes the age-gated bite observable.
    synthetic = torch.zeros(1, 49)
    synthetic[0, 8 * 3] = 1.0
    synthetic[0, 48] = 0.9
    pulse_brain = mod.OrganismBrain(302, 49, 3, 1, "cpu", seed=0)
    bites = [int(pulse_brain.act(synthetic)[0, 2].item()) for _ in range(12)]
    result = {
        "source": str(SRC.relative_to(ROOT)),
        "room_context_accuracy": float((original == world.room_context).float().mean()),
        "context_flip_fraction_after_pixel_swap": float((original != permuted).float().mean()),
        "mean_action_l1_after_swap": float((action_original - action_swapped).abs().mean()),
        "synthetic_bite_sequence": bites,
        "formula": "odd green mean > even green mean; bite gated by age remainder 5",
    }
    out = ROOT / "audit/life_strategy_probe.result.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
