"""A persistent directional state relaxes toward current visual flow."""
import torch

PARAMS = {"rate": 0.015, "decay": 0.994, "explore": 0.15, "relax": 0.35}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.device = torch.device(device)
        self.batch = batch
        self.p = {**PARAMS, **(params or {})}
        self.angles = torch.arange(16, device=self.device) * (2 * torch.pi / 16)
        self.value = torch.zeros(batch, 3, device=self.device)
        self.trace = torch.zeros(batch, 3, device=self.device)
        self.direction = torch.zeros(batch, 2, device=self.device)
        self.prev_energy = None

    def act(self, sensors):
        eyes = sensors[:, :48].reshape(self.batch, 16, 3).clamp_min(0)
        cue = eyes.sum(dim=1)
        cue = cue / cue.sum(dim=1, keepdim=True).clamp_min(1e-6)

        self.trace.mul_(float(self.p["decay"])).add_(cue)
        if sensors.shape[1] > 48:
            energy = sensors[:, 48]
            if self.prev_energy is not None:
                delta = energy - self.prev_energy
                self.value.add_(float(self.p["rate"]) * delta[:, None] * self.trace)
                self.value.clamp_(-2.5, 2.5)
            self.prev_energy = energy.clone()

        weights = torch.softmax(self.value, dim=1)
        salience = (eyes * weights[:, None, :]).sum(dim=2)
        x = (salience * torch.cos(self.angles)).sum(dim=1)
        y = (salience * torch.sin(self.angles)).sum(dim=1)
        flow = torch.stack((x, y), dim=1)
        self.direction.add_(float(self.p["relax"]) * (flow - self.direction))
        bearing = torch.atan2(self.direction[:, 1], self.direction[:, 0])
        turn = 0.7 * torch.sin(bearing)
        speed_value = 0.72 + 0.02 * (float(self.p["explore"]) - 0.15)
        speed = torch.full_like(turn, speed_value)
        bite = (salience.sum(dim=1) > 0.01).to(sensors.dtype)
        return torch.stack((turn.clamp(-1, 1), speed, bite), dim=1)

    def structure(self):
        return {"units": self.value.numel() + self.trace.numel() + self.direction.numel(), "connections": 8}
