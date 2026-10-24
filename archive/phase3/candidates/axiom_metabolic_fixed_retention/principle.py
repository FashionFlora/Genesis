"""Fixed-retention ablation of the metabolic-retention principle."""
import torch

PARAMS = {"trace_decay": 0.92, "learn_rate": 3.0, "retention_gain": 0.0, "explore_turn": 0.11}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.batch = batch
        self.p = {**PARAMS, **(params or {})}
        self.angles = torch.arange(16, device=device) * (2 * torch.pi / 16)
        self.value = torch.zeros(batch, 3, device=device)
        self.trace = torch.zeros(batch, 3, device=device)
        self.prev_energy = None
        self.prev_delta = torch.zeros(batch, device=device)
        self.clock = torch.zeros(batch, device=device)

    def act(self, sensors):
        eyes = sensors[:, :48].reshape(self.batch, 16, 3).clamp_min(0)
        energy = sensors[:, 48] if sensors.shape[1] > 48 else None
        decay = self.p["trace_decay"] + self.p["retention_gain"] * self.prev_delta
        self.trace.mul_(decay[:, None].clamp(0.5, 0.999))
        cue = eyes.sum(dim=1)
        cue = cue / cue.sum(dim=1, keepdim=True).clamp_min(1e-6)
        self.trace.add_(cue)
        if energy is not None:
            if self.prev_energy is not None:
                delta = energy - self.prev_energy + 0.001
                self.value.add_(self.p["learn_rate"] * delta[:, None] * self.trace)
                self.value.clamp_(-2.5, 2.5)
                self.prev_delta = delta.clamp(-1, 1)
            self.prev_energy = energy.clone()

        weights = torch.softmax(self.value, dim=1) * 3.0
        salience = (eyes * weights[:, None, :]).sum(dim=2)
        x = (salience * torch.cos(self.angles)).sum(dim=1)
        y = (salience * torch.sin(self.angles)).sum(dim=1)
        bearing = torch.atan2(y, x)
        strength = salience.sum(dim=1)
        self.clock += 0.037
        turn = torch.tanh(1.7 * bearing) + self.p["explore_turn"] * torch.sin(self.clock)
        speed = torch.where(strength > 0.06, torch.full_like(strength, 0.82), torch.full_like(strength, 0.62))
        bite = (strength > 1.65).to(sensors.dtype)
        return torch.stack((turn.clamp(-1, 1), speed, bite), dim=1)

    def structure(self):
        return {"units": self.value.numel() + self.trace.numel(), "connections": 6}
