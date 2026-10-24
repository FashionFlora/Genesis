"""Homeostatic color learning with direct sensory-to-motor flow."""
import torch

PARAMS = {"trace_decay": 0.92, "learn_rate": 3.0}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.batch = batch
        self.p = {**PARAMS, **(params or {})}
        self.angles = torch.arange(16, device=device) * (2 * torch.pi / 16)
        self.value = torch.zeros(batch, 3, device=device)
        self.trace = torch.zeros(batch, 3, device=device)
        self.prev_energy = None

    def act(self, sensors):
        eyes = sensors[:, :48].reshape(self.batch, 16, 3).clamp_min(0)
        cue = eyes.sum(dim=1)
        cue = cue / cue.sum(dim=1, keepdim=True).clamp_min(1e-6)
        self.trace.mul_(self.p["trace_decay"]).add_(cue)

        if sensors.shape[1] > 48:
            energy = sensors[:, 48]
            if self.prev_energy is not None:
                delta = energy - self.prev_energy
                self.value.add_(self.p["learn_rate"] * delta[:, None] * self.trace)
                self.value.clamp_(-2.5, 2.5)
            self.prev_energy = energy.clone()

        weights = torch.softmax(self.value, dim=1)
        salience = (eyes * weights[:, None, :]).sum(dim=2)
        x = (salience * torch.cos(self.angles)).sum(dim=1)
        y = (salience * torch.sin(self.angles)).sum(dim=1)
        bearing = torch.atan2(y, x)
        strength = salience.sum(dim=1)
        turn = (0.7 * torch.sin(bearing)).clamp(-1, 1)
        speed = torch.full_like(turn, 0.72)
        bite = (strength > 0.01).to(sensors.dtype)
        return torch.stack((turn, speed, bite), dim=1)

    def structure(self):
        return {"units": self.value.numel() + self.trace.numel(), "connections": 6}
