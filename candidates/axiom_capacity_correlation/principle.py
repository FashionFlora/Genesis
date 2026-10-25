"""Finite synaptic capacity redistributes strength toward persistent co-activity."""

import torch


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0):
        self.torch = torch
        self.width = n_sensors
        self.motors = n_motors
        generator = torch.Generator(device=device).manual_seed(seed)
        self.weights = torch.randn(batch, n_sensors, n_motors, device=device,
                                   generator=generator) * (n_sensors ** -0.5)
        self.capacity = self.weights.norm(dim=2, keepdim=True).clamp_min(1e-8)
        self.trace = torch.zeros_like(self.weights)
        self.previous_sensors = torch.zeros(batch, n_sensors, device=device)
        self.previous_action = torch.zeros(batch, n_motors, device=device)
        self.has_previous = torch.zeros(batch, device=device)

    def act(self, sensors):
        torch = self.torch
        pair_activity = self.previous_sensors[:, :, None] * self.previous_action[:, None, :]
        self.trace.mul_(0.99).add_(pair_activity, alpha=0.01)
        self.weights.add_(self.trace * (0.01 * self.has_previous[:, None, None]))
        norm = self.weights.norm(dim=2, keepdim=True).clamp_min(1e-8)
        self.weights.mul_(self.capacity / norm)
        action = torch.tanh(torch.einsum("bs,bsm->bm", sensors, self.weights))
        self.previous_sensors.copy_(sensors)
        self.previous_action.copy_(action.detach())
        self.has_previous.fill_(1)
        return action

    def structure(self):
        return {"units": min(self.width * self.motors, 100000),
                "connections": self.width * self.motors}
