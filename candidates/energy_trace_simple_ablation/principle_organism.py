"""Matched ablation: the single energy trace cannot learn."""

import importlib.util
from pathlib import Path


_path = Path(__file__).parents[1] / "energy_trace_simple" / "principle_organism.py"
_spec = importlib.util.spec_from_file_location("energy_trace_simple_impl", _path)
_impl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)


class OrganismBrain(_impl.OrganismBrain):
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        super().__init__(n_units, n_sensors, n_motors, batch, device, seed=seed,
                         params={"learning_rate": 0.0})
