import importlib.util
from pathlib import Path

_path = Path(__file__).parents[1] / "odkrywca_energy_turnover" / "principle.py"
_spec = importlib.util.spec_from_file_location("energy_turnover_ablation_source", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
PARAMS = {**_module.PARAMS, "turnover": 0.0}


class OrganismBrain(_module.OrganismBrain):
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        params = {**(params or {}), "turnover": 0.0}
        super().__init__(n_units, n_sensors, n_motors, batch, device, seed, params)
