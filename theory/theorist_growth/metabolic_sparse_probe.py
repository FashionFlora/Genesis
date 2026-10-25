"""Measure sparse memory growth and forgetting outside the full judge."""

import importlib.util
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[2]
candidate = ROOT / "candidates/growth_metabolic_sparse/principle_organism.py"
spec = importlib.util.spec_from_file_location("growth_metabolic_sparse", candidate)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

batch = 8
initial = []
for limit in (302, 1000, 10000, 100000):
    brain = module.OrganismBrain(limit, 49, 3, batch, "cpu")
    initial.append({"n_units": limit, **brain.structure()})

brain = module.OrganismBrain(302, 49, 3, batch, "cpu")
for _ in range(80):
    sensors = torch.rand(batch, 49)
    sensors[:, -1] = torch.rand(batch)
    brain.act(sensors)
grown = brain.structure()
for _ in range(1000):
    sensors = torch.zeros(batch, 49)
    sensors[:, -1] = 0.5
    brain.act(sensors)
quiet = brain.structure()

result = {
    "candidate": "growth_metabolic_sparse",
    "measurement": "initial memory by capacity; synthetic growth and quiet decay probe",
    "initial_by_limit": initial,
    "synthetic_growth_steps": 80,
    "grown": grown,
    "quiet_steps": 1000,
    "quiet": quiet,
    "remaining_keys": int(brain.active.sum().item()),
}
out = Path(__file__).with_suffix(".result.json")
out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
