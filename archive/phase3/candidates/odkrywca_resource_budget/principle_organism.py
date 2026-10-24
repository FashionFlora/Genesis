"""Metabolic budget: scarcity changes both movement cost and intake threshold.

The sensory learner is inherited from the homeostatic controller.  The only
new state variable is the sensed energy itself: it gates expensive wandering
and makes intake opportunistic when the reserve is low.
"""
import importlib.util
from pathlib import Path
import torch

_base_path = Path(__file__).parents[1] / "axiom_homeostasis" / "principle.py"
_spec = importlib.util.spec_from_file_location("resource_budget_base", _base_path)
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)

PARAMS = dict(_base.PARAMS)


class OrganismBrain(_base.OrganismBrain):
    USE_BUDGET = True

    def act(self, sensors):
        action = super().act(sensors)
        if not self.USE_BUDGET or sensors.shape[1] <= 48:
            return action

        eyes = sensors[:, :48].reshape(self.batch, 16, 3).clamp_min(0)
        energy = sensors[:, 48].clamp(0, 1)
        weights = torch.softmax(self.value, dim=1) * 3.0
        strength = (eyes * weights[:, None, :]).sum(dim=2).sum(dim=1)

        # Wandering is cheap only while the reserve is high.  Once a target is
        # visible, retain the parent speed so scarcity does not prevent intake.
        target_seen = strength > 0.06
        conserve = (0.42 + 0.52 * energy).clamp(0.42, 0.94)
        action[:, 1] = torch.where(target_seen, action[:, 1], action[:, 1] * conserve)

        # Scarcity lowers the evidence needed to bite.  The threshold returns
        # to the parent's 1.65 at a full reserve and bottoms at 0.70.
        threshold = 0.70 + 0.95 * energy
        action[:, 2] = (strength > threshold).to(action.dtype)
        return action

    def structure(self):
        base = super().structure()
        base["connections"] = base.get("connections", 0) + 2
        return base
