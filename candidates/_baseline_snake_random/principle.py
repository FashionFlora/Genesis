"""Seeded random actions for the Snake and Crafter control baselines."""

import random


class System:
    def __init__(self):
        self.rng = random.Random(0)

    def step(self, obs):
        return [0.5 for _ in obs]

    def act(self, obs):
        return self.rng.randrange(17 if len(obs) > 1000 else 4)

    def structure(self):
        return {"units": 0, "connections": 0, "memory_bytes": 0}
