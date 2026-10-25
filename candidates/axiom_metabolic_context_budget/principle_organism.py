"""Organism contract adapter for the finite context-budget principle."""

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "axiom_metabolic_context_budget", Path(__file__).with_name("principle.py"))
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
OrganismBrain = _module.OrganismBrain
PARAMS = _module.PARAMS
