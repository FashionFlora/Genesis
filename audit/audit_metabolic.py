"""Reproducible motor-path audit for metabolic_relaxation."""

import importlib.util
from pathlib import Path

import torch


path = Path(__file__).parents[1] / "candidates/metabolic_relaxation/principle_organism.py"
spec = importlib.util.spec_from_file_location("metabolic", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

brain = module.OrganismBrain(302, 49, 3, 1, "cpu", 0)
red = torch.zeros(1, 49)
red[0, 0] = 1.0
red[0, -1] = 0.95
first = brain.act(red)
for _ in range(20):
    brain.act(red)
print("constant_energy_action", first[0].tolist())
print("constant_energy_traces", brain.traces[0].tolist())

loss = red.clone()
loss[0, -1] = 0.90
after_loss = brain.act(loss)
print("loss_action", after_loss[0].tolist())
print("loss_traces", brain.traces[0].tolist())
