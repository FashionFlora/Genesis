"""Action credit: keep visual directions that are followed by energy gain."""

PARAMS = {"learn": 0.35, "forget": 0.985, "drive": 0.72, "bite": 0.18}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        import torch
        self.torch = torch
        self.batch = batch
        self.device = device
        self.p = {**PARAMS, **(params or {})}
        self.preference = torch.ones(batch, 3, device=device)
        self.previous_energy = None
        self.previous_color = torch.zeros(batch, 3, device=device)
        self.previous_bite = torch.zeros(batch, device=device)

    def act(self, sensors):
        torch = self.torch
        eye = sensors[:, :48].reshape(self.batch, 16, 3)
        color = eye.sum(1)
        energy = sensors[:, 48] if sensors.shape[1] > 48 else None

        # Credit only the sensory channels present before the last attempted bite.
        if energy is not None and self.previous_energy is not None:
            delta = (energy - self.previous_energy).clamp(-0.12, 0.30)
            self.preference.mul_(self.p["forget"])
            self.preference.add_(self.p["learn"] * delta[:, None] * self.previous_color
                                 * self.previous_bite[:, None])
            self.preference.clamp_(0.05, 4.0)

        weighted = eye * self.preference[:, None, :]
        strength = weighted.sum(2)
        angles = torch.arange(16, device=sensors.device, dtype=sensors.dtype)
        turn = (strength * angles.sin()).sum(1) * 2.0
        visible = strength.amax(1)
        # Keep moving while searching; bite only when a patch is close and ahead.
        center = strength[:, 15:16].maximum(strength[:, :2].amax(1, keepdim=True)).squeeze(1)
        bite = (center > self.p["bite"]).to(sensors.dtype)
        drive = torch.full_like(turn, self.p["drive"])
        out = torch.stack((turn.clamp(-1, 1), drive, bite), 1)

        self.previous_color = color.detach() / (color.sum(1, keepdim=True) + 1e-4)
        self.previous_bite = bite.detach()
        if energy is not None:
            self.previous_energy = energy.detach().clone()
        return out

    def structure(self):
        return {"units": self.preference.numel(), "connections": 16 * 3,
                "memory_bytes": self.preference.numel() * 4}
