"""Metabolic confidence: energy controls trace retention and evidence access."""

import math

import torch


PARAMS = {
    "learning_rate": 0.8,
    "forgetting": 0.997,
    "loss_gate": 0.003,
    "relaxation": 1.0,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.torch = torch
        self.batch = batch
        self.device = device
        self.pixels = (n_sensors - 1) // 3
        self.angles = torch.arange(self.pixels, device=device) * (2 * math.pi / self.pixels)
        self.params = {**PARAMS, **(params or {})}
        self.traces = torch.zeros(batch, 3, device=device)
        self.last_energy = torch.zeros(batch, device=device)
        self.last_color = torch.zeros(batch, dtype=torch.long, device=device)
        self.last_biting = torch.zeros(batch, device=device)

    def act(self, sensors):
        eye = sensors[:, :self.pixels * 3].reshape(self.batch, self.pixels, 3)
        energy = sensors[:, -1].clamp(0, 1)
        delta = energy - self.last_energy
        delta = torch.where(delta.abs() < self.params["loss_gate"], torch.zeros_like(delta), delta)
        credit = delta.clamp(-0.05, 0.2) * self.last_biting

        retention = self.params["forgetting"] ** (
            1 + self.params["relaxation"] * (1 - energy)
        )
        self.traces.mul_(retention[:, None])
        self.traces.scatter_add_(1, self.last_color[:, None], credit[:, None])

        evidence = eye.sum(dim=1)
        confidence = self.traces.abs().sum(dim=1)
        evidence_weight = 0.25 / (1 + confidence)
        color = (self.params["learning_rate"] * self.traces
                 + evidence_weight[:, None] * evidence).argmax(dim=1)
        selected = eye.gather(2, color[:, None, None].expand(-1, self.pixels, 1))[:, :, 0]
        horizontal = (selected * self.angles.cos()[None]).sum(dim=1)
        vertical = (selected * self.angles.sin()[None]).sum(dim=1)
        turn = torch.atan2(vertical, horizontal) / math.pi

        self.last_energy.copy_(energy)
        self.last_color.copy_(color)
        self.last_biting.copy_((selected.max(dim=1).values > 0.08).float())
        return torch.stack((turn, torch.full_like(turn, 0.72), self.last_biting), dim=1)

    def structure(self):
        return {"units": self.traces.shape[1], "connections": self.batch * 3}
