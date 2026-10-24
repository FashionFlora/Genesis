"""Entry point for the ablation organism contract."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("principle_organism.py")
_spec = importlib.util.spec_from_file_location("resource_budget_ablation_organism", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
OrganismBrain = _module.OrganismBrain
PARAMS = _module.PARAMS
