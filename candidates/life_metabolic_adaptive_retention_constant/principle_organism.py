"""Matched constant-retention control for H014."""

import importlib.util
from pathlib import Path

_source = (Path(__file__).resolve().parents[1] /
           "life_metabolic_adaptive_retention_budget" / "principle_organism.py")
_spec = importlib.util.spec_from_file_location("adaptive_retention", _source)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

PARAMS = dict(_module.PARAMS)
PARAMS["energy_coupling"] = 0.0


class OrganismBrain(_module.OrganismBrain):
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        merged = dict(params or {})
        merged["energy_coupling"] = 0.0
        super().__init__(n_units, n_sensors, n_motors, batch, device, seed, merged)
