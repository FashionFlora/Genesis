"""Signed action-consequence trace: losses prune sensory motor habits."""

import math

import torch


PARAMS = {
    "trace_rate": 0.8,
    "trace_decay": 0.997,
    "trace_deposit": 4.0,
    "evidence_gain": 0.25,
    "slow_speed": 0.35,
    "fed_speed": 0.80,
    "bite_threshold": 0.08,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.batch = batch
        self.device = device
        self.params = {**PARAMS, **(params or {})}
        self.pixels = (n_sensors - 1) // 3
        self.angles = torch.arange(self.pixels, device=device) * (2 * math.pi / self.pixels)
        self.trace = torch.zeros(batch, 3, 3, device=device)
        self.previous_energy = torch.zeros(batch, device=device)
        self.previous_bite = torch.zeros(batch, device=device)
        self.previous_color = torch.zeros(batch, dtype=torch.long, device=device)
        self.previous_action = torch.zeros(batch, 3, device=device)

    def act(self, sensors):
        eye = sensors[:, :self.pixels * 3].reshape(self.batch, self.pixels, 3)
        energy = sensors[:, -1].clamp(0, 1)
        gain = (energy - self.previous_energy) * self.previous_bite
        retention = 1 - self.params["trace_decay"] * (1 - energy)
        self.trace.mul_(retention[:, None, None])
        deposit = gain[:, None].clamp(-0.2, 0.2) * self.params["trace_deposit"] * self.previous_action
        self.trace.scatter_add_(1, self.previous_color[:, None, None].expand(-1, 1, 3), deposit[:, None, :])

        evidence = eye.sum(dim=1)
        expected_gain = self.trace[:, :, 1] + self.trace[:, :, 2]
        score = (self.params["trace_rate"] * energy[:, None] * expected_gain
                 + self.params["evidence_gain"] * (1 - energy[:, None]) * evidence)
        color = score.argmax(dim=1)
        selected = eye.gather(2, color[:, None, None].expand(-1, self.pixels, 1))[:, :, 0]
        horizontal = (selected * torch.cos(self.angles)[None]).sum(dim=1)
        vertical = (selected * torch.sin(self.angles)[None]).sum(dim=1)
        turn = torch.atan2(vertical, horizontal) / math.pi
        bite = (selected.max(dim=1).values > self.params["bite_threshold"]).float()
        learned_turn = self.trace.gather(1, color[:, None, None].expand(-1, 1, 3))[:, 0, 0]
        turn = (turn + 0.1 * torch.tanh(learned_turn)).clamp(-1, 1)
        speed = self.params["slow_speed"] + (self.params["fed_speed"] - self.params["slow_speed"]) * energy
        action = torch.stack((turn, speed, bite), dim=1)

        self.previous_energy.copy_(energy)
        self.previous_bite.copy_(bite)
        self.previous_color.copy_(color)
        self.previous_action.copy_(action)
        return action

    def structure(self):
        return {"units": self.trace.shape[1], "connections": self.trace.shape[1] * 3,
                "memory_bytes": self.trace.numel() * 4}
