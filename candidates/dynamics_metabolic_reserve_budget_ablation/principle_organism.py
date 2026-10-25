"""Matched control with a fixed shared memory budget."""

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "dynamics_metabolic_reserve_budget", Path(__file__).resolve().parents[1] /
    "dynamics_metabolic_reserve_budget" / "principle_organism.py")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

PARAMS = {**_module.PARAMS, "capacity_coupling": 0.0}


class OrganismBrain(_module.OrganismBrain):
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        values = {**PARAMS, **(params or {})}
        values["capacity_coupling"] = 0.0
        super().__init__(n_units, n_sensors, n_motors, batch, device, seed, values)
