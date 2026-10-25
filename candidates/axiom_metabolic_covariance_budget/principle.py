"""Metabolic covariance writes one bounded sensorimotor memory."""

import math

import torch


PARAMS = {
    "learning_rate": 0.12,
    "trace_decay": 0.985,
    "mean_decay": 0.99,
    "energy_coupling": 0.75,
    "capacity": 1.0,
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

        # The only learned object is a small channel-to-action memory.
        self.preference = torch.zeros(batch, 3, 2, device=self.device)
        self.trace = torch.zeros_like(self.preference)
        self.color_mean = torch.zeros(batch, 3, device=self.device)
        self.action_mean = torch.zeros(batch, 2, device=self.device)
        self.previous_color_delta = torch.zeros_like(self.color_mean)
        self.previous_action_delta = torch.zeros_like(self.action_mean)
        self.previous_energy = torch.zeros(batch, device=self.device)
        self.has_previous = torch.zeros(batch, device=self.device)
        self.age = torch.zeros(batch, device=self.device)
        self.phase = torch.rand(
            (batch,), device=self.device,
            generator=torch.Generator(device=self.device).manual_seed(int(seed) + 17),
        )

    def act(self, sensors):
        x = torch.as_tensor(sensors, device=self.device, dtype=torch.float32)
        eye = x[:, :self.eye_width * 3].reshape(self.batch, self.eye_width, 3)
        energy = (x[:, self.energy_index].clamp(0, 1)
                  if self.energy_index is not None else self.previous_energy)
        colors = eye.mean(dim=1)
        color_delta = colors - self.color_mean

        # Metabolic change gates eligibility; reserve changes do not name a target.
        energy_delta = (energy - self.previous_energy).clamp(-0.2, 0.2)
        forgetting = self.params["trace_decay"] + self.params["energy_coupling"] * (energy - 0.5) * 0.01
        self.trace.mul_(forgetting.clamp(0.8, 0.999)[:, None, None])
        self.trace.add_(self.previous_color_delta[:, :, None] *
                        self.previous_action_delta[:, None, :], alpha=1.0)
        self.preference.add_(self.trace * (self.params["learning_rate"] * energy_delta[:, None, None]) *
                             self.has_previous[:, None, None])

        # One global norm is the finite budget shared by every color/action pair.
        norm = self.preference.flatten(1).norm(dim=1, keepdim=True).clamp_min(1e-8)
        self.preference.mul_((self.params["capacity"] / norm).clamp(max=1.0)[:, :, None])

        rows = torch.arange(self.batch, device=self.device)
        visual = eye[:, 4:].clamp_min(0).mean(dim=1)
        selected = (visual + self.preference[:, :, 0] + 0.25 * self.preference[:, :, 1]).argmax(dim=1)
        chosen = eye[rows, :, selected].clamp_min(0)
        angles = torch.arange(self.eye_width, device=self.device) * (2 * math.pi / self.eye_width)
        vx = (chosen * angles.cos()).sum(dim=1)
        vy = (chosen * angles.sin()).sum(dim=1)
        total = chosen.sum(dim=1)
        bearing = torch.atan2(vy, vx)
        concentration = (vx.square() + vy.square()).sqrt() / (total + 1e-5)
        visible = total > 0.04
        learned = self.preference[rows, selected]
        turn = torch.where(visible, torch.tanh(2.2 * bearing + learned[:, 0]),
                           0.34 * torch.sin(self.phase + self.age * 0.031))
        drive = torch.where(visible, (total * 1.6 + learned[:, 1]).clamp(0, 0.8),
                           torch.zeros_like(total))
        bite = (visible & (concentration > 0.42) & (total > 0.24)).float()
        bite *= (self.age.remainder(5) < 1).float()

        action = torch.stack((turn.clamp(-1, 1), drive.clamp(-1, 1)), dim=1)
        action_delta = action - self.action_mean
        self.color_mean.mul_(self.params["mean_decay"]).add_(colors, alpha=1.0 - self.params["mean_decay"])
        self.action_mean.mul_(self.params["mean_decay"]).add_(action.detach(), alpha=1.0 - self.params["mean_decay"])
        self.previous_color_delta.copy_(color_delta)
        self.previous_action_delta.copy_(action_delta.detach())
        self.previous_energy.copy_(energy)
        self.has_previous.fill_(1)
        self.age += 1
        return torch.cat((action, bite[:, None]), dim=1)

    def structure(self):
        return {"units": 3, "connections": 6,
                "activity": float(self.preference.abs().mean().item())}
