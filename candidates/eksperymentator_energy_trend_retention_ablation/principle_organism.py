"""Matched control: identical brain with energy-trend trace coupling disabled."""

import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().parents[1] / "eksperymentator_energy_trend_retention" / "principle_organism.py"
_spec = importlib.util.spec_from_file_location("energy_trend_replication", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

PARAMS = dict(_module.PARAMS, trend_coupling=0.0)
OrganismBrain = _module.OrganismBrain
_original_init = OrganismBrain.__init__


def _init_control(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
    values = dict(params or {})
    values["trend_coupling"] = 0.0
    _original_init(self, n_units, n_sensors, n_motors, batch, device, seed, values)


OrganismBrain.__init__ = _init_control
