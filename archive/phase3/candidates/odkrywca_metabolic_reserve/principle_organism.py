"""Entry point alias for the metabolic reserve principle."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("principle.py")
_spec = importlib.util.spec_from_file_location("metabolic_reserve_impl", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
PARAMS = _module.PARAMS
OrganismBrain = _module.OrganismBrain
