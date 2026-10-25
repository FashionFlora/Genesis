"""A local homeostat that recalls consequence rates for sensory actions."""

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
    "turn_gain": 0.1,
    "attempt_floor": 0.05,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.batch = batch
        self.device = device
        self.pixels = (n_sensors - 1) // 3
        self.angles = torch.arange(self.pixels, device=device) * (2 * math.pi / self.pixels)
        self.params = {**PARAMS, **(params or {})}
        self.consequence = torch.zeros(batch, 3, 3, device=device)
        self.attempts = torch.zeros(batch, 3, device=device)
        self.previous_energy = torch.zeros(batch, device=device)
        self.previous_color = torch.zeros(batch, dtype=torch.long, device=device)
        self.previous_bite = torch.zeros(batch, device=device)
        self.previous_action = torch.zeros(batch, 3, device=device)

    def act(self, sensors):
        eye = sensors[:, :self.pixels * 3].reshape(self.batch, self.pixels, 3)
        energy = sensors[:, -1].clamp(0, 1)

        # One law: an eligible action writes its energetic consequence and its exposure.
        delta = energy - self.previous_energy
        eligible = self.previous_bite
        retention = 1 - self.params["trace_decay"] * (1 - energy)
        self.consequence.mul_(retention[:, None, None])
        self.attempts.mul_(retention[:, None])
        self.consequence.scatter_add_(
            1,
            self.previous_color[:, None, None].expand(-1, 1, 3),
            ((delta * eligible * self.params["trace_deposit"])[:, None] * self.previous_action)[:, None, :],
        )
        self.attempts.scatter_add_(1, self.previous_color[:, None], eligible[:, None])

        evidence = eye.sum(dim=1)
        rate = self.consequence / self.attempts.clamp_min(self.params["attempt_floor"])[:, :, None]
        score = (self.params["trace_rate"] * energy[:, None] * (rate[:, :, 1] + rate[:, :, 2])
                 + self.params["evidence_gain"] * (1 - energy[:, None]) * evidence)
        color = score.argmax(dim=1)
        selected = eye.gather(2, color[:, None, None].expand(-1, self.pixels, 1))[:, :, 0]
        horizontal = (selected * self.angles.cos()[None]).sum(dim=1)
        vertical = (selected * self.angles.sin()[None]).sum(dim=1)
        turn = torch.atan2(vertical, horizontal) / math.pi
        learned_turn = rate.gather(1, color[:, None, None].expand(-1, 1, 3))[:, 0, 0]
        turn = (turn + self.params["turn_gain"] * torch.tanh(learned_turn)).clamp(-1, 1)
        bite = (selected.max(dim=1).values > self.params["bite_threshold"]).float()

        self.previous_energy.copy_(energy)
        self.previous_color.copy_(color)
        self.previous_bite.copy_(bite)
        self.previous_action = torch.stack((turn, torch.zeros_like(turn), bite), dim=1)
        speed = self.params["slow_speed"] + (self.params["fed_speed"] - self.params["slow_speed"]) * energy
        return torch.stack((turn, speed, bite), dim=1)

    def structure(self):
        return {"units": self.consequence.shape[1], "connections": self.consequence.shape[1] * 4,
                "memory_bytes": (self.consequence.numel() + self.attempts.numel()) * 4}
