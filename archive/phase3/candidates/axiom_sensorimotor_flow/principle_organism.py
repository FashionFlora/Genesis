"""Judge entry point for the direct sensorimotor flow principle."""
from pathlib import Path
import importlib.util

path = Path(__file__).with_name("principle.py")
spec = importlib.util.spec_from_file_location("axiom_sensorimotor_flow", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
OrganismBrain = module.OrganismBrain
PARAMS = module.PARAMS
