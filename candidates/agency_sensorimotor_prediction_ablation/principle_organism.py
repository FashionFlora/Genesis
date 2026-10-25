"""Matched ablation: keep prediction state, remove its motor contribution."""

import importlib.util
from pathlib import Path


_path = Path(__file__).resolve().parents[1] / "agency_sensorimotor_prediction" / "principle_organism.py"
_spec = importlib.util.spec_from_file_location("agency_sensorimotor_prediction_impl", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

# Expose the same perturbable parameter surface as the parent candidate.
PARAMS = _module.PARAMS


class OrganismBrain(_module.OrganismBrain):
    def __init__(self, *args, **kwargs):
        params = dict(kwargs.pop("params", None) or {})
        # The EMA predictors still update and are included in structure(); only
        # their advantage is disconnected from the motor command.
        params["prediction_gain"] = 0.0
        super().__init__(*args, params=params, **kwargs)
