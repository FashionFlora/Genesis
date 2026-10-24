"""Ablation that disables action-conditioned credit."""
from pathlib import Path
import importlib.util

path = Path(__file__).parents[1] / "action_directional_credit" / "principle.py"
spec = importlib.util.spec_from_file_location("action_directional_credit_base", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class OrganismBrain(module.OrganismBrain):
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        disabled = {**(params or {}), "action_rate": 0.0}
        super().__init__(n_units, n_sensors, n_motors, batch, device, seed, disabled)


PARAMS = {**module.PARAMS, "action_rate": 0.0}
