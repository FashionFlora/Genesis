"""Judge entry point for the relaxation-flow principle."""
import importlib.util
from pathlib import Path

path = Path(__file__).with_name("principle.py")
spec = importlib.util.spec_from_file_location("axiom_relaxation_flow_principle", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
OrganismBrain = module.OrganismBrain
PARAMS = module.PARAMS
