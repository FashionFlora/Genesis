"""A slow metabolic reserve buffers hunger while allocating memory and search."""

import math
import torch

PARAMS = {
    "trace_rate": 0.8, "trace_decay": 0.997, "trace_deposit": 4.0,
    "evidence_gain": 0.25, "reserve_rate": 0.02, "bite_threshold": 0.08,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.torch, self.batch = torch, batch
        self.n_pixels = (n_sensors - 1) // 3
        self.angles = torch.arange(self.n_pixels, device=device) * (2 * math.pi / self.n_pixels)
        self.params = {**PARAMS, **(params or {})}
        self.trace = torch.zeros(batch, 3, device=device)
        self.reserve = torch.full((batch,), 0.5, device=device)
        self.previous_energy = torch.full((batch,), 0.5, device=device)
        self.previous_color = torch.zeros(batch, dtype=torch.long, device=device)
        self.previous_bite = torch.zeros(batch, device=device)

    def act(self, sensors):
        torch = self.torch
        eye = sensors[:, :self.n_pixels * 3].reshape(self.batch, self.n_pixels, 3)
        energy = sensors[:, -1].clamp(0, 1)
        self.reserve.add_(self.params["reserve_rate"] * (energy - self.reserve)).clamp_(0, 1)
        deficit = 1 - energy * self.reserve
        gain = (energy - self.previous_energy) * self.previous_bite
        self.trace.mul_((1 - self.params["trace_decay"] * deficit)[:, None])
        self.trace.scatter_add_(1, self.previous_color[:, None],
                                (gain * self.params["trace_deposit"])[:, None])
        self.trace.clamp_min_(0)
        evidence = eye.sum(dim=1)
        memory = self.params["trace_rate"] * energy[:, None] * self.reserve[:, None] * self.trace
        exploration = self.params["evidence_gain"] * deficit[:, None] * evidence
        color = (memory + exploration).argmax(dim=1)
        selected = eye.gather(2, color[:, None, None].expand(-1, self.n_pixels, 1))[:, :, 0]
        turn = torch.atan2((selected * torch.sin(self.angles)[None]).sum(dim=1),
                           (selected * torch.cos(self.angles)[None]).sum(dim=1)) / math.pi
        self.previous_energy.copy_(energy)
        self.previous_color.copy_(color)
        self.previous_bite.copy_((selected.max(dim=1).values > self.params["bite_threshold"]).float())
        return torch.stack((turn, torch.full_like(energy, 0.575), self.previous_bite), dim=1)

    def structure(self):
        return {"units": self.trace.shape[1] + 1, "connections": self.trace.shape[1] + 1}
