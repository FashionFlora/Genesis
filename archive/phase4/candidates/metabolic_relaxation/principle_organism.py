"""Local metabolic traces: energy gain reinforces, loss relaxes a cue trace."""

import math
import torch


PARAMS = {"learning_rate": 0.8, "forgetting": 0.997, "loss_gate": 0.003}
PARAMS.update({"slow_speed": 0.35, "fed_speed": 0.80})


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.torch = torch
        self.batch = batch
        self.device = device
        self.has_energy = (n_sensors % 3) == 1
        self.pixels = (n_sensors - 1) // 3 if self.has_energy else n_sensors // 3
        self.angles = torch.arange(self.pixels, device=device) * (2 * math.pi / self.pixels)
        self.params = {**PARAMS, **(params or {})}
        self.traces = torch.zeros(batch, 3, device=device)
        self.last_energy = torch.zeros(batch, device=device)
        self.last_color = torch.zeros(batch, dtype=torch.long, device=device)
        self.last_biting = torch.zeros(batch, device=device)

    def act(self, sensors):
        eye = sensors[:, :self.pixels * 3].reshape(self.batch, self.pixels, 3)
        if self.has_energy:
            energy = sensors[:, -1].clamp(0, 1)
        else:
            energy = torch.full((self.batch,), 0.5, device=self.device)
        delta = energy - self.last_energy
        delta = torch.where(delta.abs() < self.params["loss_gate"], torch.zeros_like(delta), delta)
        credit = delta.clamp(-0.05, 0.2) * self.last_biting
        self.traces.mul_(self.params["forgetting"])
        self.traces.scatter_add_(1, self.last_color[:, None], credit[:, None])

        evidence = eye.sum(dim=1)
        certainty = (self.traces.abs().sum(dim=1) > 1e-3).float()[:, None]
        color = (self.params["learning_rate"] * self.traces + 0.25 * (1 - certainty) * evidence).argmax(dim=1)
        selected = eye.gather(2, color[:, None, None].expand(-1, self.pixels, 1))[:, :, 0]
        horizontal = (selected * self.angles.cos()[None]).sum(dim=1)
        vertical = (selected * self.angles.sin()[None]).sum(dim=1)
        turn = torch.atan2(vertical, horizontal) / math.pi

        self.last_energy.copy_(energy)
        self.last_color.copy_(color)
        self.last_biting.copy_((selected.max(dim=1).values > 0.08).float())
        speed = self.params["slow_speed"] + (self.params["fed_speed"] - self.params["slow_speed"]) * energy
        return torch.stack((turn, speed, self.last_biting), dim=1)

    def structure(self):
        return {"units": self.traces.shape[1], "connections": self.batch * 3}
