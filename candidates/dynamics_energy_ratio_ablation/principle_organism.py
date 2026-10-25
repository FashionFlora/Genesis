"""Matched ablation for normalized energy dynamics."""

from pathlib import Path
import importlib.util

_path = Path(__file__).parents[1] / "dynamics_energy_ratio" / "principle_organism.py"
_spec = importlib.util.spec_from_file_location("dynamics_energy_ratio_impl", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
OrganismBrain = _module.OrganismBrain
PARAMS = {**_module.PARAMS, "credit_scale": 0.0}
