"""A two-state local homeostat: useful color traces grow, costly bites fade."""

import math

import torch


PARAMS = {
    "trace_rate": 0.8,
    "trace_decay": 0.997,
    "trace_deposit": 4.0,
    "cost_rate": 0.7,
    "cost_decay": 0.995,
    "evidence_gain": 0.25,
    "bite_threshold": 0.08,
    "cost_threshold": 0.018,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.torch, self.batch = torch, batch
        self.n_pixels = (n_sensors - 1) // 3
        self.angles = torch.arange(self.n_pixels, device=device) * (2 * math.pi / self.n_pixels)
        self.params = {**PARAMS, **(params or {})}
        self.trace = torch.zeros(batch, 3, device=device)
        self.cost = torch.zeros(batch, 3, device=device)
        self.previous_energy = torch.zeros(batch, device=device)
        self.previous_color = torch.zeros(batch, dtype=torch.long, device=device)
        self.previous_bite = torch.zeros(batch, device=device)

    def act(self, sensors):
        torch = self.torch
        eye = sensors[:, :self.n_pixels * 3].reshape(self.batch, self.n_pixels, 3)
        energy = sensors[:, -1].clamp(0, 1)
        delta = energy - self.previous_energy
        useful = (delta * self.previous_bite).clamp_min(0)
        costly = ((-delta - self.params["cost_threshold"]).clamp_min(0)
                  * self.previous_bite)
        self.trace.mul_(1 - self.params["trace_decay"] * (1 - energy)[:, None])
        self.cost.mul_(self.params["cost_decay"])
        self.trace.scatter_add_(1, self.previous_color[:, None],
                                (useful * self.params["trace_deposit"])[:, None])
        self.cost.scatter_add_(1, self.previous_color[:, None],
                               (costly * self.params["cost_rate"])[:, None])
        evidence = eye.sum(dim=1)
        score = (self.params["trace_rate"] * energy[:, None] * self.trace
                 - self.cost + self.params["evidence_gain"] * (1 - energy[:, None]) * evidence)
        color = score.argmax(dim=1)
        selected = eye.gather(2, color[:, None, None].expand(-1, self.n_pixels, 1))[:, :, 0]
        horizontal = (selected * torch.cos(self.angles)[None]).sum(dim=1)
        vertical = (selected * torch.sin(self.angles)[None]).sum(dim=1)
        turn = torch.atan2(vertical, horizontal) / math.pi
        self.previous_energy.copy_(energy)
        self.previous_color.copy_(color)
        self.previous_bite.copy_((selected.max(dim=1).values > self.params["bite_threshold"]).float())
        return torch.stack((turn, torch.full_like(energy, 0.575), self.previous_bite), dim=1)

    def structure(self):
        return {"units": self.trace.shape[1] * 2, "connections": self.trace.shape[1] * 2}
