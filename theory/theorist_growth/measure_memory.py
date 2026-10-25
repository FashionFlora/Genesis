"""Measure persistent candidate tensor storage at several capacity limits."""

import importlib.util
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[2]
candidate_path = ROOT / "candidates/growth_local_eligibility/principle_organism.py"
spec = importlib.util.spec_from_file_location("growth_local_eligibility", candidate_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

batch = 1024
rows = []
for limit in (302, 1000, 10000, 100000):
    brain = module.OrganismBrain(limit, 49, 5, batch, "cpu")
    shared = brain.angles.numel() * brain.angles.element_size()
    batched = sum(value.numel() * value.element_size()
                  for name, value in vars(brain).items()
                  if torch.is_tensor(value) and name != "angles")
    rows.append({"n_units": limit, "batch": batch,
                 "per_organism_state_bytes": batched // batch,
                 "shared_tensor_bytes": shared,
                 "persistent_tensor_bytes": batched + shared})

result = {"candidate": "growth_local_eligibility", "device": "cpu",
          "measurement": "persistent tensor storage at initialization",
          "sizes": rows}
out = Path(__file__).with_name("memory_measurement.json")
out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(out)
