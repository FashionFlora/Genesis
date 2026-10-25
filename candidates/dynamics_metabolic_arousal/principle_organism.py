"""A slow metabolic arousal state couples viability to sensorimotor gain."""

import math

import torch


PARAMS = {
    "learning_rate": 0.35,
    "trace_forgetting": 0.06,
    "preference_forgetting": 0.002,
    "energy_coupling": 0.75,
    "reserve_rate": 0.04,
    "arousal_rate": 0.08,
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
        self.preference = torch.zeros(batch, 3, device=self.device)
        self.eligibility = torch.zeros_like(self.preference)
        self.previous_color = torch.zeros(batch, dtype=torch.long, device=self.device)
        self.previous_energy = torch.zeros(batch, device=self.device)
        self.reserve = torch.full((batch,), 0.5, device=self.device)
        self.arousal = torch.full((batch,), 0.5, device=self.device)
        if self.energy_index is None:
            self.previous_energy.fill_(0.5)

    def act(self, sensors):
        x = torch.as_tensor(sensors, device=self.device, dtype=torch.float32)
        eye = x[:, :self.eye_width * 3].reshape(self.batch, self.eye_width, 3)
        has_energy = self.energy_index is not None
        energy = (x[:, self.energy_index].clamp(0, 1)
                  if has_energy else torch.full((self.batch,), 0.5, device=self.device))
        delta = (energy - self.previous_energy).clamp(-0.2, 0.2)

        # The reserve supplies a local surprise signal for trace lifetime.
        contrast = (energy - self.reserve).clamp(-0.5, 0.5)
        coupling = float(self.params["energy_coupling"]) if has_energy else 0.0
        self.reserve.add_(self.params["reserve_rate"] * contrast)
        forget = self.params["trace_forgetting"] * (1.0 + coupling * contrast)
        self.eligibility.mul_((1.0 - forget).clamp(0.8, 0.999)[:, None])
        rows = torch.arange(self.batch, device=self.device)
        self.eligibility[rows, self.previous_color] += 1.0
        self.preference.mul_(1.0 - self.params["preference_forgetting"])
        self.preference.add_(self.eligibility * delta[:, None], alpha=self.params["learning_rate"])
        self.preference.clamp_(-2.0, 2.0)

        # Arousal is a bounded slow state: scarcity raises gain, abundance lowers it.
        target = (0.5 + 1.2 * (0.5 - energy)).clamp(0.0, 1.0)
        self.arousal.add_(self.params["arousal_rate"] * coupling * (target - self.arousal))
        gain = 0.5 + coupling * (self.arousal - 0.5)

        visual = eye[:, 4:].clamp_min(0).mean(dim=1)
        selected = (self.preference + visual).argmax(dim=1)
        chosen = eye[rows, :, selected].clamp_min(0)
        angle = torch.arange(self.eye_width, device=self.device) * (2 * math.pi / self.eye_width)
        vx = (chosen * angle.cos()).sum(dim=1)
        vy = (chosen * angle.sin()).sum(dim=1)
        total = chosen.sum(dim=1)
        bearing = torch.atan2(vy, vx)
        concentration = (vx.square() + vy.square()).sqrt() / (total + 1e-5)
        visible = total > 0.04
        turn = torch.where(visible, torch.tanh((1.8 + 0.8 * gain) * bearing), torch.zeros_like(total))
        drive = torch.where(visible, (total * (1.3 + 0.8 * gain)).clamp(0, 0.8), torch.zeros_like(total))
        threshold = (0.26 - 0.08 * gain).clamp(0.12, 0.32)
        bite = (visible & (concentration > 0.42) & (total > threshold)).float()

        self.previous_color.copy_(selected)
        self.previous_energy.copy_(energy)
        return torch.stack((turn.clamp(-1, 1), drive.clamp(-1, 1), bite), dim=1)

    def structure(self):
        return {"units": 3, "connections": 3}
