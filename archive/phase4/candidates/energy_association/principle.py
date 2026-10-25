"""Metabolic selection: food-driven energy changes strengthen sensory habits."""

import math

import torch


PARAMS = {"rate": 0.8, "decay": 0.997}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.torch = torch
        self.batch = batch
        self.device = device
        self.n_pixels = (n_sensors - 1) // 3
        self.angles = torch.arange(self.n_pixels, device=device) * (2 * math.pi / self.n_pixels)
        self.params = {**PARAMS, **(params or {})}
        self.preference = torch.zeros(batch, 3, device=device)
        self.previous_energy = torch.zeros(batch, device=device)
        self.previous_color = torch.zeros(batch, dtype=torch.long, device=device)
        self.previous_bite = torch.zeros(batch, device=device)

    def act(self, sensors):
        torch = self.torch
        eye = sensors[:, :self.n_pixels * 3].reshape(self.batch, self.n_pixels, 3)
        energy = sensors[:, -1]

        gain = energy - self.previous_energy
        update = gain * self.previous_bite
        self.preference.mul_(self.params["decay"])
        self.preference.scatter_add_(1, self.previous_color[:, None], update[:, None])

        evidence = eye.sum(dim=1)
        uncertainty = (self.preference.abs().sum(dim=1) < 1e-3).float()[:, None]
        color = (self.preference * self.params["rate"] + 0.25 * uncertainty * evidence).argmax(dim=1)
        selected = eye.gather(2, color[:, None, None].expand(-1, self.n_pixels, 1))[:, :, 0]
        horizontal = (selected * torch.cos(self.angles)[None]).sum(dim=1)
        vertical = (selected * torch.sin(self.angles)[None]).sum(dim=1)
        turn = torch.atan2(vertical, horizontal) / math.pi

        self.previous_energy.copy_(energy)
        self.previous_color.copy_(color)
        self.previous_bite.copy_((selected.max(dim=1).values > 0.08).float())
        return torch.stack((turn, torch.full_like(turn, 0.72), self.previous_bite), dim=1)

    def structure(self):
        return {"units": self.preference.shape[1], "connections": self.preference.shape[1]}
