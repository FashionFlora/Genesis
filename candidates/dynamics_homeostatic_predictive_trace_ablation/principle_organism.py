"""Matched ablation: fixed-scale energy trace without volatility coupling."""

from pathlib import Path

_source = Path(__file__).resolve().parents[1] / "dynamics_homeostatic_predictive_trace" / "principle_organism.py"
exec(compile(_source.read_text(), str(_source), "exec"), globals())

_Base = OrganismBrain


class OrganismBrain(_Base):
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        merged = {"volatility_coupling": 0.0, "normalization_gain": 0.0}
        if params:
            merged.update(params)
        super().__init__(n_units, n_sensors, n_motors, batch, device, seed, merged)
