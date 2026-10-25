"""Check whether action_consequence changes behavior before its trace is trained."""

import importlib.util
from pathlib import Path

import torch


path = Path(__file__).parents[1] / "candidates/action_consequence/principle_organism.py"
spec = importlib.util.spec_from_file_location("action", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

brain = module.OrganismBrain(302, 49, 3, 1, "cpu", 0)
red = torch.zeros(1, 49)
red[0, 0] = 1.0
red[0, -1] = 0.95
first = brain.act(red)
for _ in range(20):
    last = brain.act(red)
print("constant_energy_action", first[0].tolist())
print("constant_energy_action_after_20", last[0].tolist())
print("constant_energy_trace_norm", float(brain.trace[0].abs().sum()))
