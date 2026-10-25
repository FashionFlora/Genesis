"""Matched control without the shared preference-capacity projection."""

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "axiom_metabolic_context_budget", Path(__file__).resolve().parents[1] /
    "axiom_metabolic_context_budget" / "principle.py")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

PARAMS = {**_module.PARAMS, "capacity": 1e6}


class OrganismBrain(_module.OrganismBrain):
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        values = {**PARAMS, **(params or {})}
        values["capacity"] = 1e6
        super().__init__(n_units, n_sensors, n_motors, batch, device, seed, values)
