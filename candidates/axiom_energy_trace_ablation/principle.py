"""Matched ablation: the synaptic eligibility trace never changes weights."""

import torch


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0):
        self.torch = torch
        self.batch = batch
        self.width = n_sensors
        self.motors = n_motors
        self.generator = torch.Generator(device=device).manual_seed(seed)
        self.weights = torch.randn(batch, n_sensors, n_motors, device=device,
                                   generator=self.generator) * (n_sensors ** -0.5)
        self.trace = torch.zeros(batch, n_sensors, n_motors, device=device)
        self.previous_sensors = torch.zeros(batch, n_sensors, device=device)
        self.previous_action = torch.zeros(batch, n_motors, device=device)
        self.previous_energy = torch.zeros(batch, device=device)
        self.has_previous = torch.zeros(batch, device=device)

    def act(self, sensors):
        torch = self.torch
        energy = sensors[:, -1].clamp(0, 1)
        delta = (energy - self.previous_energy).clamp(-0.2, 0.2)
        credit = delta * self.has_previous
        eligibility = self.previous_sensors[:, :, None] * self.previous_action[:, None, :]
        self.trace.mul_(0.985).add_(eligibility, alpha=0.015)
        prediction = torch.einsum("bs,bsm->bm", sensors, self.weights)
        action = torch.tanh(prediction)
        self.previous_sensors.copy_(sensors)
        self.previous_action.copy_(action.detach())
        self.previous_energy.copy_(energy)
        self.has_previous.fill_(1)
        return action

    def structure(self):
        return {"units": min(self.width * self.motors, 100000),
                "connections": self.width * self.motors}
