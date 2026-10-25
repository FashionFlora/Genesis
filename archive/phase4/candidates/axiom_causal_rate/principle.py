"""Value cues by their recent internal-energy change per bite attempt."""

import math

import torch


PARAMS = {
    "trace_decay": 0.997,
    "trace_rate": 0.8,
    "trace_deposit": 4.0,
    "evidence_gain": 0.25,
    "bite_threshold": 0.08,
    "speed": 0.575,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.batch = batch
        self.device = device
        self.has_energy = n_sensors % 3 == 1
        self.pixels = (n_sensors - int(self.has_energy)) // 3
        self.angles = torch.arange(self.pixels, device=device) * (2 * math.pi / self.pixels)
        self.params = {**PARAMS, **(params or {})}
        self.consequence = torch.zeros(batch, 3, device=device)
        self.attempts = torch.zeros(batch, 3, device=device)
        self.previous_energy = torch.zeros(batch, device=device)
        self.previous_color = torch.zeros(batch, dtype=torch.long, device=device)
        self.previous_bite = torch.zeros(batch, device=device)

    def act(self, sensors):
        eye = sensors[:, :self.pixels * 3].reshape(self.batch, self.pixels, 3)
        energy = sensors[:, -1].clamp(0, 1) if self.has_energy else torch.zeros(
            self.batch, device=self.device)
        delta = energy - self.previous_energy

        self.consequence.mul_(self.params["trace_decay"])
        self.attempts.mul_(self.params["trace_decay"])
        eligible = self.previous_bite
        self.consequence.scatter_add_(
            1, self.previous_color[:, None],
            (delta * eligible * self.params["trace_deposit"])[:, None])
        self.attempts.scatter_add_(1, self.previous_color[:, None], eligible[:, None])

        evidence = eye.sum(dim=1)
        rate = self.consequence / self.attempts.clamp_min(0.02)
        memory = self.params["trace_rate"] * energy[:, None] * rate
        exploration = self.params["evidence_gain"] * (1 - energy[:, None]) * evidence
        color = (memory + exploration).argmax(dim=1)
        selected = eye.gather(2, color[:, None, None].expand(-1, self.pixels, 1))[:, :, 0]
        horizontal = (selected * self.angles.cos()[None]).sum(dim=1)
        vertical = (selected * self.angles.sin()[None]).sum(dim=1)
        turn = torch.atan2(vertical, horizontal) / math.pi
        bite = (selected.max(dim=1).values > self.params["bite_threshold"]).float()

        self.previous_energy.copy_(energy)
        self.previous_color.copy_(color)
        self.previous_bite.copy_(bite)
        speed = torch.full_like(energy, self.params["speed"])
        return torch.stack((turn, speed, bite), dim=1)

    def structure(self):
        return {"units": 6, "connections": 6}
