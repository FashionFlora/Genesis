"""Organism contract adapter for the matched no-plasticity ablation."""

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("axiom_energy_trace_ablation", Path(__file__).with_name("principle.py"))
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
OrganismBrain = _module.OrganismBrain
