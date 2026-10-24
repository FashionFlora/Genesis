"""Judge entry point for the learning ablation."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("principle.py")
_spec = importlib.util.spec_from_file_location("axiom_homeostasis_nolearn_principle", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
OrganismBrain = _module.OrganismBrain
PARAMS = _module.PARAMS
