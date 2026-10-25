"""Matched controller with metabolic evidence disabled."""

from theory.theorist_life.metabolic_color_ratio.principle_organism import OrganismBrain as BaseBrain


class OrganismBrain(BaseBrain):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params["metabolic_credit"] = 0.0
