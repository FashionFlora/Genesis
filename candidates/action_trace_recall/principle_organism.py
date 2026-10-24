"""Outcome-weighted action traces recall movements in familiar sensory contexts."""

import math

import torch


PARAMS = {"value_rate": 0.75, "trace_decay": 0.995, "value_decay": 0.998}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.batch = batch
        self.device = device
        self.params = {**PARAMS, **(params or {})}
        self.pixels = (n_sensors - 1) // 3
        self.angles = torch.arange(self.pixels, device=device) * (2 * math.pi / self.pixels)
        self.value = torch.zeros(batch, 3, device=device)
        self.trace = torch.zeros(batch, 3, 3, device=device)
        self.trace_mass = torch.zeros(batch, 3, device=device)
        self.previous_energy = torch.zeros(batch, device=device)
        self.previous_bite = torch.zeros(batch, device=device)
        self.previous_color = torch.zeros(batch, dtype=torch.long, device=device)
        self.previous_action = torch.zeros(batch, 3, device=device)

    def act(self, sensors):
        eye = sensors[:, :self.pixels * 3].reshape(self.batch, self.pixels, 3)
        energy = sensors[:, -1]
        delta = ((energy - self.previous_energy) * self.previous_bite).clamp(-0.05, 0.2)
        self.value.mul_(self.params["value_decay"])
        self.value.scatter_add_(1, self.previous_color[:, None],
                                (self.params["value_rate"] * delta)[:, None])
        self.trace.mul_(self.params["trace_decay"])
        self.trace_mass.mul_(self.params["trace_decay"])
        self.trace.scatter_add_(1, self.previous_color[:, None, None].expand(-1, 1, 3),
                                delta[:, None, None] * self.previous_action[:, None, :])
        self.trace_mass.scatter_add_(1, self.previous_color[:, None], delta.abs()[:, None])

        evidence = eye.sum(dim=1)
        uncertainty = (self.value.abs().sum(dim=1) < 1e-3).float()[:, None]
        color = (self.value + 0.25 * uncertainty * evidence).argmax(dim=1)
        selected = eye.gather(2, color[:, None, None].expand(-1, self.pixels, 1))[:, :, 0]
        horizontal = (selected * torch.cos(self.angles)[None]).sum(dim=1)
        vertical = (selected * torch.sin(self.angles)[None]).sum(dim=1)
        visual_turn = torch.atan2(vertical, horizontal) / math.pi
        bite = (selected.max(dim=1).values > 0.08).float()

        remembered = self.trace.gather(1, color[:, None, None].expand(-1, 1, 3))[:, 0]
        mass = self.trace_mass.gather(1, color[:, None])
        confidence = mass / (mass + 0.05)
        remembered_turn = remembered[:, 0] / mass[:, 0].clamp_min(1e-6)
        remembered_speed = remembered[:, 1] / mass[:, 0].clamp_min(1e-6)
        turn = ((1 - confidence[:, 0]) * visual_turn + confidence[:, 0] * remembered_turn).clamp(-1, 1)
        speed = ((1 - confidence[:, 0]) * 0.72 + confidence[:, 0] * remembered_speed).clamp(0, 1)
        action = torch.stack((turn, speed, bite), dim=1)
        self.previous_energy.copy_(energy)
        self.previous_bite.copy_(bite)
        self.previous_color.copy_(color)
        self.previous_action.copy_(action)
        return action

    def structure(self):
        return {"units": 12, "connections": self.batch * 12,
                "memory_bytes": self.batch * 12 * 8}
