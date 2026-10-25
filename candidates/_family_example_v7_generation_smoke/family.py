"""A delta-trace controller family with four evolvable parameters."""

import math

import torch


GENOME = {
    "trace_decay": (0.90, 0.999),
    "evidence_gain": (0.02, 0.80),
    "speed": (0.1, 1.0),
    "bite_threshold": (0.01, 0.35),
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, genome=None):
        self.batch = batch
        self.device = device
        self.channels = 3
        self.pixels = (n_sensors - 1) // self.channels
        self.angles = torch.arange(self.pixels, device=device) * (2 * math.pi / self.pixels)
        self.genome = genome or {
            "trace_decay": torch.full((batch,), 0.97, device=device),
            "evidence_gain": torch.full((batch,), 0.25, device=device),
            "speed": torch.full((batch,), 0.6, device=device),
            "bite_threshold": torch.full((batch,), 0.08, device=device),
        }
        self.trace = torch.zeros(batch, self.channels, device=device)
        self.previous_energy = torch.zeros(batch, device=device)
        self.previous_color = torch.zeros(batch, dtype=torch.long, device=device)
        self.previous_bite = torch.zeros(batch, device=device)

    def act(self, sensors):
        eye = sensors[:, :self.pixels * self.channels].reshape(self.batch, self.pixels, self.channels)
        energy = sensors[:, -1].clamp(0, 1)
        gain = (energy - self.previous_energy) * self.previous_bite
        self.trace.mul_(self.genome["trace_decay"][:, None])
        self.trace.scatter_add_(1, self.previous_color[:, None], gain.clamp(-0.05, 0.2)[:, None])
        evidence = eye.sum(1)
        confidence = (self.trace.abs().sum(1) > 0.001).float()[:, None]
        color = (self.trace + self.genome["evidence_gain"][:, None] *
                 (1 - confidence) * evidence).argmax(1)
        selected = eye.gather(2, color[:, None, None].expand(-1, self.pixels, 1))[:, :, 0]
        x = (selected * self.angles.cos()).sum(1)
        y = (selected * self.angles.sin()).sum(1)
        turn = torch.atan2(y, x) / math.pi
        speed = self.genome["speed"] * (energy > 0.15)
        bite = (selected.max(1).values > self.genome["bite_threshold"]).float()
        self.previous_energy.copy_(energy)
        self.previous_color.copy_(color)
        self.previous_bite.copy_(bite)
        return torch.stack((turn, speed, bite), dim=1)

    def structure(self):
        return {"units": self.pixels * 3 + self.channels, "connections": self.pixels * self.channels}
