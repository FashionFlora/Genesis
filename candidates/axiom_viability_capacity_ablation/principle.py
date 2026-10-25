"""Matched frozen-weight ablation for axiom_viability_capacity."""

import torch


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0):
        self.width = int(n_sensors)
        self.motors = int(n_motors)
        generator = torch.Generator(device=device).manual_seed(int(seed))
        self.weights = torch.randn(batch, self.width, self.motors, device=device,
                                   generator=generator) * (self.width ** -0.5)

    def act(self, sensors):
        return torch.tanh(torch.einsum("bs,bsm->bm", sensors, self.weights))

    def structure(self):
        return {"units": min(self.width * self.motors, 100000),
                "connections": self.width * self.motors}
