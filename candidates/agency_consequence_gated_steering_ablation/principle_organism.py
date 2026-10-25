"""Matched ablation: retain consequence estimates but disconnect policy gating."""

import importlib.util
from pathlib import Path


_path = Path(__file__).resolve().parents[1] / "agency_consequence_gated_steering" / "principle_organism.py"
_spec = importlib.util.spec_from_file_location("agency_consequence_gated_steering_impl", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
PARAMS = _module.PARAMS


class OrganismBrain(_module.OrganismBrain):
    def __init__(self, *args, **kwargs):
        params = dict(kwargs.pop("params", None) or {})
        params["prediction_gain"] = 0.0
        super().__init__(*args, params=params, **kwargs)
