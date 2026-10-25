"""Ablation: preserve growth_trace behavior but remove its structural signal."""

import importlib.util
from pathlib import Path


_source = Path(__file__).resolve().parents[1] / "growth_trace" / "principle_organism.py"
_spec = importlib.util.spec_from_file_location("growth_trace_source", _source)
_growth = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_growth)
PARAMS = _growth.PARAMS


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.brain = _growth.OrganismBrain(n_units, n_sensors, n_motors, batch, device,
                                           seed=seed, params=params)

    def act(self, sensors):
        return self.brain.act(sensors)

    def structure(self):
        return {"units": 2.0, "connections": 2.0}
