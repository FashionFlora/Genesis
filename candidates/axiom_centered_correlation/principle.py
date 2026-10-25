"""Finite synaptic capacity learns deviations from expected co-activity."""

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
        self.sensor_mean = torch.zeros(batch, n_sensors, device=device)
        self.action_mean = torch.zeros(batch, n_motors, device=device)
        self.previous_sensor_delta = torch.zeros_like(self.sensor_mean)
        self.previous_action_delta = torch.zeros_like(self.action_mean)
        self.has_previous = torch.zeros(batch, device=device)

    def act(self, sensors):
        torch = self.torch
        sensor_delta = sensors - self.sensor_mean
        action = torch.tanh(torch.einsum("bs,bsm->bm", sensors, self.weights))
        action_delta = action - self.action_mean
        pair_activity = self.previous_sensor_delta[:, :, None] * self.previous_action_delta[:, None, :]
        self.trace.mul_(0.99).add_(pair_activity, alpha=0.01)
        self.weights.add_(self.trace * (0.01 * self.has_previous[:, None, None]))
        norm = self.weights.norm(dim=2, keepdim=True).clamp_min(1e-8)
        self.weights.mul_(self.capacity / norm)
        self.sensor_mean.mul_(0.99).add_(sensors, alpha=0.01)
        self.action_mean.mul_(0.99).add_(action.detach(), alpha=0.01)
        self.previous_sensor_delta.copy_(sensor_delta)
        self.previous_action_delta.copy_(action_delta.detach())
        self.has_previous.fill_(1)
        return action

    def structure(self):
        return {"units": min(self.width * self.motors, 100000),
                "connections": self.width * self.motors}
