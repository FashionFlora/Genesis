"""Expose metabolic_gate behavior before any trace has been learned."""

import importlib.util
from pathlib import Path

import torch


path = Path(__file__).parents[1] / "candidates/metabolic_gate/principle_organism.py"
spec = importlib.util.spec_from_file_location("gate", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

brain = module.OrganismBrain(302, 49, 3, 1, "cpu", 0)
for energy in (0.0, 0.5, 0.95):
    eye = torch.zeros(1, 49)
    eye[0, 0] = 1.0
    eye[0, -1] = energy
    action = brain.act(eye)
    print("energy", energy, "action", action[0].tolist(), "trace", brain.trace[0].tolist())
