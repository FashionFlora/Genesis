"""Candidate wrapper for the biology developmental switch."""
import importlib.util
from pathlib import Path

_source = Path(__file__).resolve().parents[2] / "biology" / "developmental_metabolic_organism.py"
_spec = importlib.util.spec_from_file_location("developmental_metabolic_organism", _source)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
OrganismBrain = _module.OrganismBrain
PARAMS = _module.PARAMS

__all__ = ["OrganismBrain", "PARAMS"]
