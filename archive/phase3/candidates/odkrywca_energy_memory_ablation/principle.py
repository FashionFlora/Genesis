"""Entry point alias for the ablation control."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("principle_organism.py")
_spec = importlib.util.spec_from_file_location("energy_memory_ablation_organism", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

PARAMS = _module.PARAMS
OrganismBrain = _module.OrganismBrain
