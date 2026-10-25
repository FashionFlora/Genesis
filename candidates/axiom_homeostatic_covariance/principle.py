"""Energy-gated centered covariance under a fixed per-sensor synaptic budget."""

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
        self.previous_energy = torch.zeros(batch, device=device)
        self.has_previous = torch.zeros(batch, device=device)

    def act(self, sensors):
        torch = self.torch
        energy = sensors[:, -1].clamp(0, 1)
        sensor_delta = sensors - self.sensor_mean
        action = torch.tanh(torch.einsum("bs,bsm->bm", sensors, self.weights))
        action_delta = action - self.action_mean

        centered_pair = (self.previous_sensor_delta[:, :, None]
                         * self.previous_action_delta[:, None, :])
        self.trace.mul_(0.985).add_(centered_pair, alpha=0.015)
        energy_change = (energy - self.previous_energy).clamp(-0.2, 0.2)
        update = 0.06 * energy_change[:, None, None] * self.trace
        self.weights.add_(update * self.has_previous[:, None, None])

        norm = self.weights.norm(dim=2, keepdim=True).clamp_min(1e-8)
        self.weights.mul_(self.capacity / norm)
        self.sensor_mean.mul_(0.99).add_(sensors, alpha=0.01)
        self.action_mean.mul_(0.99).add_(action.detach(), alpha=0.01)
        self.previous_sensor_delta.copy_(sensor_delta)
        self.previous_action_delta.copy_(action_delta.detach())
        self.previous_energy.copy_(energy)
        self.has_previous.fill_(1)
        return action

    def structure(self):
        return {"units": min(self.width * self.motors, 100000),
                "connections": self.width * self.motors}
