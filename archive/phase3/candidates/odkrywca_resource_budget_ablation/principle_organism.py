"""Ablation: homeostatic learner without metabolic budget modulation."""
import importlib.util
from pathlib import Path

_path = Path(__file__).parents[1] / "odkrywca_resource_budget" / "principle_organism.py"
_spec = importlib.util.spec_from_file_location("resource_budget_parent", _path)
_parent = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_parent)

PARAMS = dict(_parent.PARAMS)


class OrganismBrain(_parent.OrganismBrain):
    USE_BUDGET = False
