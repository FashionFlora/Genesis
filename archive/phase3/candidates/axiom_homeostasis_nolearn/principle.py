"""Ablation: preserve the controller, disable energy-based trace learning."""
import importlib.util
from pathlib import Path

_base_path = Path(__file__).parents[1] / "axiom_homeostasis" / "principle.py"
_spec = importlib.util.spec_from_file_location("axiom_homeostasis_base", _base_path)
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)


class OrganismBrain(_base.OrganismBrain):
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        disabled = {**(params or {}), "learn_rate": 0.0}
        super().__init__(n_units, n_sensors, n_motors, batch, device, seed, disabled)


PARAMS = {**_base.PARAMS, "learn_rate": 0.0}
