"""Check that inactive sparse associations disappear without a separate schedule."""
import importlib.util
import json
from pathlib import Path

import torch

path = Path(__file__).resolve().parents[2] / "candidates/growth_local_eligibility/principle_organism.py"
spec = importlib.util.spec_from_file_location("growth_candidate", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
brain = module.OrganismBrain(302, 49, 3, 8, "cpu")
for _ in range(80):
    sensors = torch.rand(8, 49)
    sensors[:, -1] = torch.rand(8)
    brain.act(sensors)
grown = brain.structure()
for _ in range(1000):
    sensors = torch.zeros(8, 49)
    sensors[:, -1] = 0.5
    brain.act(sensors)
quiet = brain.structure()
result = {"growth_steps": 80, "quiet_steps": 1000,
          "grown": grown, "quiet": quiet, "remaining_keys": len(brain.keys)}
Path(__file__).with_suffix(".result.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
