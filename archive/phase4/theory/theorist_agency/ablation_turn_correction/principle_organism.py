"""Ablation of motor-memory steering from the action-consequence homeostat."""

import math

import torch


PARAMS = {
    "trace_rate": 0.8,
    "trace_decay": 0.997,
    "trace_deposit": 4.0,
    "loss_deposit": 2.0,
    "loss_gate": 0.005,
    "evidence_gain": 0.25,
    "slow_speed": 0.35,
    "fed_speed": 0.80,
    "bite_threshold": 0.08,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.batch = batch
        self.device = device
        self.pixels = (n_sensors - 1) // 3
        self.angles = torch.arange(self.pixels, device=device) * (2 * math.pi / self.pixels)
        self.params = {**PARAMS, **(params or {})}
        self.trace = torch.zeros(batch, 3, device=device)
        self.action_trace = torch.zeros(batch, 3, 3, device=device)
        self.previous_energy = torch.zeros(batch, device=device)
        self.previous_color = torch.zeros(batch, dtype=torch.long, device=device)
        self.previous_bite = torch.zeros(batch, device=device)
        self.previous_action = torch.zeros(batch, 3, device=device)

    def act(self, sensors):
        eye = sensors[:, :self.pixels * 3].reshape(self.batch, self.pixels, 3)
        energy = sensors[:, -1].clamp(0, 1)

        delta = energy - self.previous_energy
        useful = torch.where(delta > self.params["loss_gate"],
                             delta * self.params["trace_deposit"],
                             torch.where(delta < -self.params["loss_gate"],
                                         delta * self.params["loss_deposit"],
                                         torch.zeros_like(delta))) * self.previous_bite
        retention = 1 - self.params["trace_decay"] * (1 - energy)
        self.trace.mul_(retention[:, None])
        self.trace.scatter_add_(1, self.previous_color[:, None], useful[:, None])
        self.action_trace.mul_(retention[:, None, None])
        self.action_trace.scatter_add_(
            1, self.previous_color[:, None, None].expand(-1, 1, 3),
            useful[:, None, None] * self.previous_action[:, None, :],
        )

        evidence = eye.sum(dim=1)
        memory = self.params["trace_rate"] * energy[:, None] * self.trace
        exploration = self.params["evidence_gain"] * (1 - energy[:, None]) * evidence
        color = (memory + exploration).argmax(dim=1)
        selected = eye.gather(2, color[:, None, None].expand(-1, self.pixels, 1))[:, :, 0]
        horizontal = (selected * self.angles.cos()[None]).sum(dim=1)
        vertical = (selected * self.angles.sin()[None]).sum(dim=1)
        turn = (torch.atan2(vertical, horizontal) / math.pi).clamp(-1, 1)
        bite = (selected.max(dim=1).values > self.params["bite_threshold"]).float()

        self.previous_energy.copy_(energy)
        self.previous_color.copy_(color)
        self.previous_bite.copy_(bite)
        self.previous_action = torch.stack((turn, torch.zeros_like(turn), bite), dim=1)
        speed = self.params["slow_speed"] + (self.params["fed_speed"] - self.params["slow_speed"]) * energy
        return torch.stack((turn, speed, bite), dim=1)

    def structure(self):
        return {"units": self.trace.shape[1], "connections": self.trace.shape[1] * 4}
