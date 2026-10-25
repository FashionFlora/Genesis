"""Action consequence trace: sensory directions gain value after energetic outcomes."""

import math

import torch


PARAMS = {"value_rate": 0.75, "trace_decay": 0.995, "value_decay": 0.998}


class System:
    def __init__(self):
        self.width = 0

    def step(self, obs):
        self.width = len(obs)
        return [0.5 for _ in obs]

    def structure(self):
        return {"units": self.width, "connections": self.width * 3}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.torch = torch
        self.batch = batch
        self.device = device
        self.params = {**PARAMS, **(params or {})}
        self.pixels = (n_sensors - 1) // 3
        self.angles = torch.arange(self.pixels, device=device) * (2 * math.pi / self.pixels)
        self.value = torch.zeros(batch, 3, device=device)
        self.trace = torch.zeros(batch, 3, 3, device=device)
        self.previous_energy = torch.zeros(batch, device=device)
        self.previous_bite = torch.zeros(batch, device=device)
        self.previous_color = torch.zeros(batch, dtype=torch.long, device=device)
        self.previous_action = torch.zeros(batch, 3, device=device)
        self.ready = torch.zeros(batch, dtype=torch.bool, device=device)

    def act(self, sensors):
        eye = sensors[:, :self.pixels * 3].reshape(self.batch, self.pixels, 3)
        energy = sensors[:, -1]
        if self.ready.any():
            delta = (energy - self.previous_energy) * self.previous_bite
            self.value.mul_(self.params["value_decay"])
            self.value.scatter_add_(1, self.previous_color[:, None],
                                    (self.params["value_rate"] * delta.clamp(-0.05, 0.2))[:, None])
            self.trace.mul_(self.params["trace_decay"])
            self.trace.scatter_add_(1, self.previous_color[:, None, None].expand(-1, 1, 3),
                                    (delta[:, None, None] * self.previous_action[:, None, :]))

        evidence = eye.sum(dim=1)
        uncertainty = (self.value.abs().sum(dim=1) < 1e-3).float()[:, None]
        scores = self.value + 0.25 * uncertainty * evidence
        color = scores.argmax(dim=1)
        selected = eye.gather(2, color[:, None, None].expand(-1, self.pixels, 1))[:, :, 0]
        horizontal = (selected * torch.cos(self.angles)[None]).sum(dim=1)
        vertical = (selected * torch.sin(self.angles)[None]).sum(dim=1)
        turn = torch.atan2(vertical, horizontal) / math.pi
        bite = (selected.max(dim=1).values > 0.08).float()
        action = torch.stack((turn, torch.full_like(turn, 0.72), bite), dim=1)

        self.previous_energy.copy_(energy)
        self.previous_bite.copy_(bite)
        self.previous_color.copy_(color)
        self.previous_action.copy_(action)
        self.ready.fill_(True)
        return action

    def structure(self):
        return {"units": 9, "connections": self.batch * 9,
                "memory_bytes": self.batch * 9 * 8}
