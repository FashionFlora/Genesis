"""A metabolic stock gates retention, sensory exploration, and movement."""

import math

import torch


PARAMS = {
    "trace_rate": 0.8,
    "trace_decay": 0.997,
    "trace_deposit": 4.0,
    "evidence_gain": 0.25,
    "slow_speed": 0.35,
    "fed_speed": 0.80,
    "bite_threshold": 0.08,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.torch = torch
        self.batch = batch
        self.device = device
        self.n_pixels = (n_sensors - 1) // 3
        self.angles = torch.arange(self.n_pixels, device=device) * (2 * math.pi / self.n_pixels)
        self.params = {**PARAMS, **(params or {})}
        self.trace = torch.zeros(batch, 3, device=device)
        self.previous_energy = torch.zeros(batch, device=device)
        self.previous_color = torch.zeros(batch, dtype=torch.long, device=device)
        self.previous_bite = torch.zeros(batch, device=device)

    def act(self, sensors):
        torch = self.torch
        eye = sensors[:, :self.n_pixels * 3].reshape(self.batch, self.n_pixels, 3)
        energy = sensors[:, -1].clamp(0, 1)

        gain = (energy - self.previous_energy) * self.previous_bite
        retention = 1 - self.params["trace_decay"] * (1 - energy)
        self.trace.mul_(retention[:, None])
        self.trace.scatter_add_(1, self.previous_color[:, None],
                                (gain * self.params["trace_deposit"])[:, None])
        self.trace.clamp_min_(0)

        evidence = eye.sum(dim=1)
        memory = self.params["trace_rate"] * energy[:, None] * self.trace
        exploration = self.params["evidence_gain"] * (1 - energy[:, None]) * evidence
        color = (memory + exploration).argmax(dim=1)
        selected = eye.gather(2, color[:, None, None].expand(-1, self.n_pixels, 1))[:, :, 0]
        horizontal = (selected * torch.cos(self.angles)[None]).sum(dim=1)
        vertical = (selected * torch.sin(self.angles)[None]).sum(dim=1)
        turn = torch.atan2(vertical, horizontal) / math.pi

        self.previous_energy.copy_(energy)
        self.previous_color.copy_(color)
        self.previous_bite.copy_((selected.max(dim=1).values > self.params["bite_threshold"]).float())
        speed = self.params["slow_speed"] + (self.params["fed_speed"] - self.params["slow_speed"]) * energy
        return torch.stack((turn, speed, self.previous_bite), dim=1)

    def structure(self):
        return {"units": self.trace.shape[1], "connections": self.trace.shape[1]}
