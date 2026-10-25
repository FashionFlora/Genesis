"""Action consequences add a small motor-memory correction to a metabolic homeostat."""

import torch


PARAMS = {"value_rate": 0.8, "value_decay": 0.998}


class System:
    def __init__(self):
        self.width = 0

    def step(self, obs):
        self.width = len(obs)
        return [0.5 for _ in obs]

    def structure(self):
        return {"units": self.width, "connections": self.width * 3}

