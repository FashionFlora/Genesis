"""Predictive local dynamics: retain traces during expected energy drift, prune on surprise."""

import math

import torch


PARAMS = {
    "learning_rate": 0.35,
    "trace_forgetting": 0.06,
    "preference_forgetting": 0.002,
    "surprise_coupling": 4.0,
    "delta_prediction_rate": 0.08,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.device = torch.device(device)
        self.batch = int(batch)
        self.params = {**PARAMS, **(params or {})}
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
        self.previous_energy = torch.full((batch,), 0.5, device=self.device)
        self.predicted_delta = torch.zeros(batch, device=self.device)
        self.has_energy_sample = torch.zeros(batch, dtype=torch.bool, device=self.device)

    def act(self, sensors):
        x = torch.as_tensor(sensors, device=self.device, dtype=torch.float32)
        eye = x[:, :self.eye_width * 3].reshape(self.batch, self.eye_width, 3)
        if self.energy_index is None:
            energy = torch.full((self.batch,), 0.5, device=self.device)
        else:
            energy = x[:, self.energy_index].clamp(0, 1)

        raw_delta = (energy - self.previous_energy).clamp(-0.2, 0.2)
        delta = torch.where(self.has_energy_sample, raw_delta, torch.zeros_like(raw_delta))
        # A local predictive state separates expected metabolism from surprise.
        prediction_error = (delta - self.predicted_delta).abs()
        self.predicted_delta.lerp_(delta, float(self.params["delta_prediction_rate"]))
        surprise = prediction_error.clamp(0, 0.2)
        forgetting = self.params["trace_forgetting"] * (
            1.0 + float(self.params["surprise_coupling"]) * surprise)
        self.eligibility.mul_((1.0 - forgetting).clamp(0.8, 0.999)[:, None, None])

        rows = torch.arange(self.batch, device=self.device)
        green = eye[:, :, 1]
        even = green[:, 0:4:2].mean(dim=1)
        odd = green[:, 1:4:2].mean(dim=1)
        context = (odd > even).long()
        self.eligibility[rows, self.previous_color, self.previous_context] += 1.0
        self.preference.mul_(1.0 - self.params["preference_forgetting"])
        self.preference.add_(self.eligibility * delta[:, None, None], alpha=self.params["learning_rate"])
        self.preference.clamp_(-2.0, 2.0)

        visual = eye[:, 4:].clamp_min(0).mean(dim=1)
        selected = (self.preference[rows, :, context] + visual).argmax(dim=1)
        chosen = eye[rows, :, selected].clamp_min(0)
        angles = torch.arange(self.eye_width, device=self.device) * (2 * math.pi / self.eye_width)
        vx = (chosen * angles.cos()).sum(dim=1)
        vy = (chosen * angles.sin()).sum(dim=1)
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
