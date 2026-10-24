"""Action flux: energy change reinforces all eligible sensor-motor associations."""

PARAMS = {"learn": 0.18, "trace": 0.90, "decay": 0.995, "drive": 0.70, "bite": 0.18}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        import torch
        self.torch = torch
        self.batch = batch
        self.p = {**PARAMS, **(params or {})}
        self.preference = torch.ones(batch, 3, 3, device=device)
        self.eligibility = torch.zeros(batch, 3, 3, device=device)
        self.previous_energy = None
        self.previous_color = torch.zeros(batch, 3, device=device)
        self.previous_action = torch.zeros(batch, 3, device=device)
        self.angles = torch.arange(16, device=device) * (2 * torch.pi / 16)

    def act(self, sensors):
        torch = self.torch
        eye = sensors[:, :48].reshape(self.batch, 16, 3)
        energy = sensors[:, 48] if sensors.shape[1] > 48 else None
        color = eye.sum(1)
        color = color / (color.sum(1, keepdim=True) + 1e-4)

        if energy is not None and self.previous_energy is not None:
            delta = (energy - self.previous_energy).clamp(-0.12, 0.30)
            self.eligibility.mul_(self.p["trace"]).add_(
                self.previous_color[:, :, None] * self.previous_action[:, None, :])
            self.preference.add_(self.p["learn"] * delta[:, None, None] * self.eligibility)
            self.preference.mul_(self.p["decay"]).clamp_(0.05, 4.0)

        weighted = eye * self.preference.mean(2)[:, None, :]
        strength = weighted.sum(2)
        turn = (strength * self.angles.sin()).sum(1) * 2.0
        center = strength[:, 15:16].maximum(strength[:, :2].amax(1, keepdim=True)).squeeze(1)
        bite = (center > self.p["bite"]).to(sensors.dtype)
        drive = torch.full_like(turn, self.p["drive"])
        action = torch.stack((turn.clamp(-1, 1), drive, bite), 1)

        self.previous_color = color.detach()
        self.previous_action = action.detach()
        if energy is not None:
            self.previous_energy = energy.detach().clone()
        return action

    def structure(self):
        return {"units": self.preference.numel(), "connections": 3 * 3,
                "memory_bytes": self.preference.numel() * 4 + self.eligibility.numel() * 4}
