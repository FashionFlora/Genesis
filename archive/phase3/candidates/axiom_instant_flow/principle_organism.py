"""Judge entry point for immediate sensorimotor coupling."""
import importlib.util
from pathlib import Path

path = Path(__file__).with_name("principle.py")
spec = importlib.util.spec_from_file_location("axiom_instant_flow_principle", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
OrganismBrain = module.OrganismBrain
PARAMS = module.PARAMS
