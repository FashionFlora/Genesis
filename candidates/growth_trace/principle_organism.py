"""Sparse growth/pruning through persistent color-energy associations."""

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("growth_family", Path(__file__).with_name("family.py"))
_family = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_family)

PARAMS = {
    "trace_decay": 0.9076170325279236,
    "evidence_gain": 0.22142334282398224,
    "speed": 0.11176100373268127,
    "bite_threshold": 0.15729780495166779,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        chosen = {**PARAMS, **(params or {})}
        genome = {key: _family.torch.full((batch,), value, device=device)
                  for key, value in chosen.items()}
        self.brain = _family.OrganismBrain(n_units, n_sensors, n_motors, batch, device,
                                           seed=seed, genome=genome)

    def act(self, sensors):
        return self.brain.act(sensors)

    def structure(self):
        return self.brain.structure()
