"""Matched control: predictive surprise does not alter trace lifetime."""

import importlib.util
from pathlib import Path

_MAIN_PATH = Path(__file__).resolve().parents[1] / "dynamics_surprise_retention" / "principle_organism.py"
_SPEC = importlib.util.spec_from_file_location("surprise_retention_main", _MAIN_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
_MainBrain = _MODULE.OrganismBrain
_MAIN_PARAMS = _MODULE.PARAMS

PARAMS = {**_MAIN_PARAMS, "surprise_coupling": 0.0}


class OrganismBrain(_MainBrain):
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        chosen = {**(params or {}), "surprise_coupling": 0.0}
        super().__init__(n_units, n_sensors, n_motors, batch, device, seed, chosen)
