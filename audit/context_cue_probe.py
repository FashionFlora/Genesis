"""Measure whether the life candidate's context bit decodes the world cue."""

import json
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sandbox.worlds.organism import OrganismWorld


def measure(seed, batch=256):
    world = OrganismWorld(batch=batch, device="cpu", seed=seed)
    rows = []
    for _ in range(3):
        sensors = world.observe()
        eye = sensors[:, :48].reshape(batch, 16, 3)
        all_pixels = (eye[:, 1::2, 1].mean(1) > eye[:, 0::2, 1].mean(1)).long()
        first_four = (eye[:, 1:4:2, 1].mean(1) > eye[:, 0:4:2, 1].mean(1)).long()
        rows.append({
            "all_pixel_accuracy": float((all_pixels == world.room_context).float().mean()),
            "first_four_accuracy": float((first_four == world.room_context).float().mean()),
            "room_zero_fraction": float((world.room == 0).float().mean()),
        })
        world.step(torch.zeros(batch, 3))
    return rows


def main():
    result = {str(seed): measure(seed) for seed in (7, 19, 123)}
    flat = [row for rows in result.values() for row in rows]
    result["summary"] = {
        "mean_all_pixel_accuracy": sum(r["all_pixel_accuracy"] for r in flat) / len(flat),
        "mean_first_four_accuracy": sum(r["first_four_accuracy"] for r in flat) / len(flat),
        "n_batches": len(flat),
        "formula": "odd green mean > even green mean",
    }
    path = ROOT / "audit/context_cue_probe.result.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
