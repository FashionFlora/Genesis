"""Energy-shaped shared memory budget for local color-context traces."""

import math

import torch


PARAMS = {
    "learning_rate": 0.36,
    "trace_decay": 0.94,
    "preference_decay": 0.998,
    "capacity": 0.5,
    "reserve_rate": 0.04,
    "capacity_coupling": 0.8,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.device = torch.device(device)
        self.batch = int(batch)
        self.eye_width = int(n_sensors) // 3
        self.has_energy = int(n_sensors) > self.eye_width * 3
        self.energy_index = self.eye_width * 3
        self.params = {**PARAMS, **(params or {})}
        self.preference = torch.zeros(batch, 3, 2, device=self.device)
        self.eligibility = torch.zeros_like(self.preference)
        self.previous_color = torch.zeros(batch, dtype=torch.long, device=self.device)
        self.previous_context = torch.zeros(batch, dtype=torch.long, device=self.device)
        self.previous_energy = torch.full((batch,), 0.5, device=self.device)
        self.reserve = torch.full((batch,), 0.5, device=self.device)
        self.age = torch.zeros(batch, device=self.device)
        self.phase = torch.rand((batch,), device=self.device,
                                generator=torch.Generator(device=self.device).manual_seed(int(seed) + 17))

    def act(self, sensors):
        x = torch.as_tensor(sensors, device=self.device, dtype=torch.float32)
        eye = x[:, :self.eye_width * 3].reshape(self.batch, self.eye_width, 3)
        if self.has_energy:
            energy = x[:, self.energy_index].clamp(0, 1)
        else:
            energy = self.reserve

        # The reserve is a slow local state; it shapes one shared memory budget.
        rate = float(self.params["reserve_rate"])
        self.reserve.add_((energy - self.reserve) * rate)
        delta = (energy - self.previous_energy).clamp(-0.2, 0.2)
        rows = torch.arange(self.batch, device=self.device)
        forget = float(self.params["trace_decay"])
        self.eligibility.mul_(forget)
        self.eligibility[rows, self.previous_color, self.previous_context] += 1.0
        self.preference.mul_(float(self.params["preference_decay"]))
        credit = delta * (0.45 + 0.55 * energy)
        self.preference.add_(self.eligibility * credit[:, None, None],
                             alpha=float(self.params["learning_rate"]))

        # Scarcity expands the same finite norm available to all contexts.
        coupling = float(self.params["capacity_coupling"])
        budget = float(self.params["capacity"]) * (1.0 + coupling * (0.5 - self.reserve) * 2.0)
        budget = budget.clamp_min(0.05)
        norm = self.preference.flatten(1).norm(dim=1, keepdim=True).clamp_min(1e-8)
        self.preference.mul_((budget[:, None] / norm).clamp(max=1.0)[:, :, None])

        green = eye[:, :, 1]
        even = green[:, 0::2].mean(dim=1)
        odd = green[:, 1::2].mean(dim=1)
        context = (odd > even).long()
        visual = eye[:, 4:].clamp_min(0).mean(dim=1)
        selected = (visual + self.preference[rows, :, context]).argmax(dim=1)
        chosen = eye[rows, :, selected].clamp_min(0)
        angles = torch.arange(self.eye_width, device=self.device) * (2 * math.pi / self.eye_width)
        vx = (chosen * angles.cos()).sum(dim=1)
        vy = (chosen * angles.sin()).sum(dim=1)
        total = chosen.sum(dim=1)
        bearing = torch.atan2(vy, vx)
        concentration = (vx.square() + vy.square()).sqrt() / (total + 1e-5)
        visible = total > 0.04
        urgency = (1.0 + (0.35 - energy).clamp_min(0) * 1.5).clamp(1.0, 1.5)
        turn = torch.where(visible, torch.tanh(2.2 * urgency * bearing),
                           0.34 * torch.sin(self.phase + self.age * 0.031))
        drive = torch.where(visible, (total * (1.45 + 0.35 * (energy < 0.35))).clamp(0, 0.8),
                            torch.zeros_like(total))
        bite = visible & (concentration > 0.42) & (total > 0.24)
        bite = bite.float() * (self.age.remainder(5) < 1).float()

        self.previous_color.copy_(selected)
        self.previous_context.copy_(context)
        self.previous_energy.copy_(energy)
        self.age += 1
        return torch.stack((turn.clamp(-1, 1), drive.clamp(-1, 1), bite), dim=1)

    def structure(self):
        return {"units": 3, "connections": 6,
                "activity": float(self.preference.abs().mean().item())}
