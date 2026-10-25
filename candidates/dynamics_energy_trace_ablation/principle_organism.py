"""Local eligibility dynamics for energy-guided color selection."""

import math
import torch


PARAMS = {
    "learning_rate": 0.0,
    "trace_forgetting": 0.06,
    "preference_forgetting": 0.002,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.device = torch.device(device)
        self.batch = int(batch)
        self.params = dict(PARAMS)
        if params:
            self.params.update(params)
        n_sensors = int(n_sensors)
        if n_sensors % 3 == 0:
            self.eye_width = n_sensors // 3
            self.energy_index = None
        elif (n_sensors - 1) % 3 == 0:
            self.eye_width = (n_sensors - 1) // 3
            self.energy_index = n_sensors - 1
        else:
            raise ValueError("sensors must contain RGB pixels and optional energy")
        self.preference = torch.zeros(batch, 3, 2, device=self.device)
        self.eligibility = torch.zeros_like(self.preference)
        self.previous_color = torch.zeros(batch, dtype=torch.long, device=self.device)
        self.previous_context = torch.zeros(batch, dtype=torch.long, device=self.device)
        self.previous_energy = torch.zeros(batch, device=self.device)
        self.age = torch.zeros(batch, device=self.device)

    def act(self, sensors):
        x = torch.as_tensor(sensors, device=self.device, dtype=torch.float32)
        eye = x[:, :self.eye_width * 3].reshape(self.batch, self.eye_width, 3)
        energy = (x[:, self.energy_index].clamp(0, 1)
                  if self.energy_index is not None else torch.zeros(self.batch, device=self.device))

        even = eye[:, 0:4:2, 1].mean(dim=1)
        odd = eye[:, 1:4:2, 1].mean(dim=1)
        context = (odd > even).long()
        delta = (energy - self.previous_energy).clamp(-0.2, 0.2)

        self.eligibility.mul_(1.0 - self.params["trace_forgetting"])
        rows = torch.arange(self.batch, device=self.device)
        self.eligibility[rows, self.previous_color, self.previous_context] += 1.0
        self.preference.mul_(1.0 - self.params["preference_forgetting"])
        self.preference.add_(self.eligibility * delta[:, None, None], alpha=self.params["learning_rate"])
        self.preference.clamp_(-2.0, 2.0)

        visual = eye[:, 4:].clamp_min(0).mean(dim=1)
        selected = (self.preference[rows, :, context] + visual).argmax(dim=1)
        chosen = eye[rows, :, selected].clamp_min(0)
        angle = torch.arange(self.eye_width, device=self.device) * (2 * math.pi / self.eye_width)
        vx = (chosen * angle.cos()).sum(dim=1)
        vy = (chosen * angle.sin()).sum(dim=1)
        total = chosen.sum(dim=1)
        bearing = torch.atan2(vy, vx)
        concentration = (vx.square() + vy.square()).sqrt() / (total + 1e-5)
        visible = total > 0.04
        turn = torch.where(visible, torch.tanh(2.2 * bearing), 0.35 * torch.sin(self.age * 0.031))
        drive = torch.where(visible, (total * 1.6).clamp(0, 0.8), torch.zeros_like(total))
        bite = (visible & (concentration > 0.42) & (total > 0.24)).float()
        bite *= (self.age.remainder(5) < 1).float()

        self.previous_color.copy_(selected)
        self.previous_context.copy_(context)
        self.previous_energy.copy_(energy)
        self.age += 1
        return torch.stack((turn.clamp(-1, 1), drive.clamp(-1, 1), bite), dim=1)

    def structure(self):
        return {"units": 3, "connections": 6}
