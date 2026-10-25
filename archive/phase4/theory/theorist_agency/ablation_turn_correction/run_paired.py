"""Small CPU probe for the motor-memory steering ablation."""

import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "sandbox"))
from organism_judge import load_brain, run_life
from worlds.organism import OrganismWorld


torch.set_num_threads(1)
batch = 8
device = "cpu"
paths = {
    "parent": ROOT / "candidates/action_consequence_homeostat/principle_organism.py",
    "ablation": Path(__file__).parent / "principle_organism.py",
}
totals = {name: [] for name in paths}
for seed in range(4):
    for name, path in paths.items():
        brain = load_brain(path, 302, batch, device, seed + 1729,
                           OrganismWorld.N_SENSORS)[1]
        life = run_life(brain, batch, device, seed * 101 + 7,
                        steps=6000, n_units=302)
        totals[name].append(sum(sample["rooms_reached"] for sample in life["samples"]) / batch)
result = {name: {"per_seed": values, "mean_rooms": sum(values) / len(values)}
          for name, values in totals.items()}
result["protocol"] = {"batch": batch, "seeds": 4, "steps": 6000,
                      "units": 302, "device": device}
result_path = Path(__file__).parent / "paired_probe.json"
result_path.write_text(json.dumps(result, sort_keys=True) + "\n")
print(result)
