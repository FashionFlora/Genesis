"""Judge entry point for action-conditioned energy credit."""
from pathlib import Path
import importlib.util

path = Path(__file__).with_name("principle.py")
spec = importlib.util.spec_from_file_location("action_directional_credit_principle", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
OrganismBrain = module.OrganismBrain
PARAMS = module.PARAMS
