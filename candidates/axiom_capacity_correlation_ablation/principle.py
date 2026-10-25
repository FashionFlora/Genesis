"""Matched ablation: finite synaptic capacity without correlation learning."""

import torch


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0):
        self.width = n_sensors
        self.motors = n_motors
        generator = torch.Generator(device=device).manual_seed(seed)
        self.weights = torch.randn(batch, n_sensors, n_motors, device=device,
                                   generator=generator) * (n_sensors ** -0.5)

    def act(self, sensors):
        return torch.tanh(torch.einsum("bs,bsm->bm", sensors, self.weights))

    def structure(self):
        return {"units": min(self.width * self.motors, 100000),
                "connections": self.width * self.motors}
