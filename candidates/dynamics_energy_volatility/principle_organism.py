"""Energy-volatility-controlled lifetime for local eligibility."""

import math

import torch


PARAMS = {
    "learning_rate": 0.35,
    "trace_forgetting": 0.06,
    "preference_forgetting": 0.002,
    "volatility_coupling": 4.0,
    "volatility_smoothing": 0.05,
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
        self.volatility = torch.zeros(batch, device=self.device)
        self.has_energy_sample = torch.zeros(batch, dtype=torch.bool, device=self.device)

    def act(self, sensors):
        x = torch.as_tensor(sensors, device=self.device, dtype=torch.float32)
        eye = x[:, :self.eye_width * 3].reshape(self.batch, self.eye_width, 3)
        energy = (x[:, self.energy_index].clamp(0, 1)
                  if self.energy_index is not None else torch.zeros(self.batch, device=self.device))
        raw_delta = energy - self.previous_energy
        delta = torch.where(self.has_energy_sample, raw_delta, torch.zeros_like(raw_delta)).clamp(-0.2, 0.2)

        smoothing = float(self.params["volatility_smoothing"])
        self.volatility.lerp_(delta.abs(), smoothing)
        coupling = float(self.params["volatility_coupling"])
        forget = self.params["trace_forgetting"] * (1.0 + coupling * self.volatility)
        self.eligibility.mul_((1.0 - forget).clamp(0.8, 0.999)[:, None, None])
        rows = torch.arange(self.batch, device=self.device)
        even = eye[:, 0:4:2, 1].mean(dim=1)
        odd = eye[:, 1:4:2, 1].mean(dim=1)
        context = (odd > even).long()
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
        turn = torch.where(visible, torch.tanh(2.2 * bearing), torch.zeros_like(total))
        drive = torch.where(visible, (total * 1.6).clamp(0, 0.8), torch.zeros_like(total))
        bite = (visible & (concentration > 0.42) & (total > 0.24)).float()

        self.previous_color.copy_(selected)
        self.previous_context.copy_(context)
        self.previous_energy.copy_(energy)
        self.has_energy_sample.fill_(True)
        return torch.stack((turn.clamp(-1, 1), drive.clamp(-1, 1), bite), dim=1)

    def structure(self):
        return {"units": 3, "connections": 6}
