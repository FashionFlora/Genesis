"""Homeostatic trace: endogenous energy error selects and revises sensory habits."""

import math

import torch


PARAMS = {
    "gain": 0.8,
    "failure": 0.45,
    "decay": 0.995,
    "explore_after": 7.0,
    "explore_steps": 24.0,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.batch = batch
        self.device = device
        self.n_units = n_units
        self.n_pixels = n_sensors // 3
        self.angles = torch.arange(self.n_pixels, device=device) * (2 * math.pi / self.n_pixels)
        self.params = {**PARAMS, **(params or {})}
        self.trace = torch.zeros(batch, 3, device=device)
        self.previous_energy = torch.zeros(batch, device=device)
        self.previous_color = torch.zeros(batch, dtype=torch.long, device=device)
        self.previous_bite = torch.zeros(batch, device=device)
        self.failures = torch.zeros(batch, device=device)
        self.explore = torch.zeros(batch, device=device)
        self.ready = torch.zeros(batch, dtype=torch.bool, device=device)

    def act(self, sensors):
        eye = sensors[:, :self.n_pixels * 3].reshape(self.batch, self.n_pixels, 3)
        energy = sensors[:, -1]
        if self.ready.any():
            delta = energy - self.previous_energy
            success = self.previous_bite * (delta > 0.01).float()
            failure = self.previous_bite * (delta <= 0.01).float()
            self.trace.mul_(self.params["decay"])
            self.trace.scatter_add_(1, self.previous_color[:, None],
                                    (self.params["gain"] * success
                                     - self.params["failure"] * failure)[:, None])
            self.failures = torch.where(success > 0, self.failures * 0.25,
                                        self.failures + failure)
            trigger = self.failures >= self.params["explore_after"]
            self.explore = torch.where(trigger,
                                       torch.full_like(self.explore, self.params["explore_steps"]),
                                       (self.explore - 1).clamp_min(0))
            self.failures = torch.where(trigger, torch.zeros_like(self.failures), self.failures)

        evidence = eye.sum(dim=1)
        uncertain = self.trace.abs().sum(dim=1) < 0.35
        exploratory = (self.explore > 0) | uncertain
        learned = self.trace + 0.22 * evidence
        color = learned.argmax(dim=1)
        cycle = (self.previous_color + 1) % 3
        color = torch.where(exploratory, cycle, color)
        selected = eye.gather(2, color[:, None, None].expand(-1, self.n_pixels, 1))[:, :, 0]
        horizontal = (selected * torch.cos(self.angles)[None]).sum(dim=1)
        vertical = (selected * torch.sin(self.angles)[None]).sum(dim=1)
        turn = torch.atan2(vertical, horizontal) / math.pi
        bite = (selected.max(dim=1).values > 0.08).float()
        self.previous_energy.copy_(energy)
        self.previous_color.copy_(color)
        self.previous_bite.copy_(bite)
        self.ready.fill_(True)
        return torch.stack((turn, torch.full_like(turn, 0.72), bite), dim=1)

    def structure(self):
        return {"units": self.n_units, "connections": self.n_units * 3,
                "memory_bytes": self.n_units * 16}
