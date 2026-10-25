"""Signed metabolic tags bind a sensory color to the preceding action."""

import math

import torch


PARAMS = {
    "trace_rate": 0.8,
    "trace_decay": 0.997,
    "trace_deposit": 4.0,
    "evidence_gain": 0.25,
    "bite_threshold": 0.08,
    "speed": 0.575,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.batch = batch
        self.device = device
        self.params = {**PARAMS, **(params or {})}
        self.pixels = (n_sensors - 1) // 3
        self.angles = torch.arange(self.pixels, device=device) * (2 * math.pi / self.pixels)
        self.trace = torch.zeros(batch, 3, 3, device=device)
        self.mass = torch.zeros(batch, 3, device=device)
        self.previous_energy = torch.zeros(batch, device=device)
        self.previous_color = torch.zeros(batch, dtype=torch.long, device=device)
        self.previous_bite = torch.zeros(batch, device=device)
        self.previous_action = torch.zeros(batch, 3, device=device)

    def act(self, sensors):
        eye = sensors[:, :self.pixels * 3].reshape(self.batch, self.pixels, 3)
        energy = sensors[:, -1].clamp(0, 1)
        delta = (energy - self.previous_energy) * self.previous_bite

        self.trace.mul_(self.params["trace_decay"])
        self.mass.mul_(self.params["trace_decay"])
        deposit = delta[:, None, None] * self.previous_action[:, None, :] * self.params["trace_deposit"]
        self.trace.scatter_add_(1, self.previous_color[:, None, None].expand(-1, 1, 3), deposit)
        self.mass.scatter_add_(1, self.previous_color[:, None], delta.abs()[:, None])

        evidence = eye.sum(dim=1)
        confidence = self.mass / (self.mass + 0.05)
        remembered_value = self.trace / self.mass.clamp_min(1e-6)[:, :, None]
        score = (self.params["trace_rate"] * energy[:, None] * self.mass
                 + self.params["evidence_gain"] * (1 - energy[:, None]) * evidence)
        color = score.argmax(dim=1)
        selected = eye.gather(2, color[:, None, None].expand(-1, self.pixels, 1))[:, :, 0]
        horizontal = (selected * self.angles.cos()[None]).sum(dim=1)
        vertical = (selected * self.angles.sin()[None]).sum(dim=1)
        visual_turn = torch.atan2(vertical, horizontal) / math.pi
        remembered = remembered_value.gather(1, color[:, None, None].expand(-1, 1, 3))[:, 0]
        recall = confidence.gather(1, color[:, None])[:, 0]
        turn = ((1 - recall) * visual_turn + recall * remembered[:, 0]).clamp(-1, 1)
        bite = (selected.max(dim=1).values > self.params["bite_threshold"]).float()

        self.previous_energy.copy_(energy)
        self.previous_color.copy_(color)
        self.previous_bite.copy_(bite)
        self.previous_action.copy_(torch.stack((turn, torch.full_like(turn, self.params["speed"]), bite), dim=1))
        return self.previous_action.clone()

    def structure(self):
        return {"units": self.trace.shape[1], "connections": self.trace.numel(),
                "memory_bytes": self.trace.numel() * 4}
