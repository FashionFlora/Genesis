"""Fixed-lifetime control for reserve-coupled local eligibility traces."""

import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().parents[1] / "dynamics_metabolic_retention" / "principle_organism.py"
_spec = importlib.util.spec_from_file_location("metabolic_retention", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)


PARAMS = dict(_module.PARAMS, energy_coupling=0.0)
OrganismBrain = _module.OrganismBrain
_original_init = OrganismBrain.__init__


def _init_fixed(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
    values = dict(params or {})
    values["energy_coupling"] = 0.0
    _original_init(self, n_units, n_sensors, n_motors, batch, device, seed, values)


OrganismBrain.__init__ = _init_fixed
