"""Local plasticity whose eligibility trace is paid for by current energy."""

PARAMS = {"rate": 0.02, "trace_decay": 0.96, "weight_decay": 0.9999}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        import torch

        self.torch = torch
        self.n = n_units
        self.batch = batch
        self.device = device
        self.energy_sensor = n_sensors > 48
        self.p = {**PARAMS, **(params or {})}
        gen = torch.Generator(device=device).manual_seed(seed)
        self.receptors = torch.randn(n_sensors, n_units, device=device, generator=gen) / n_sensors**0.5
        self.weights = torch.randn(batch, n_units, n_motors, device=device, generator=gen)
        self.weights *= 0.18 / n_units**0.5
        self.trace = torch.zeros(batch, n_units, device=device)
        self.previous_features = None
        self.previous_action = None
        self.previous_energy = None

    def act(self, sensors):
        torch = self.torch
        features = torch.tanh(sensors @ self.receptors)
        energy = sensors[:, -1] if self.energy_sensor else torch.zeros(self.batch, device=self.device)
        if self.previous_energy is not None:
            gain = energy - self.previous_energy
            # Eligibility is retained only in proportion to the resource that can pay for it.
            self.trace.mul_(self.p["trace_decay"]).add_(self.previous_features * energy[:, None])
            update = (self.p["rate"] * gain / (energy + 0.05))[:, None, None]
            self.weights.add_(update * self.trace[:, :, None] * self.previous_action[:, None, :])
            self.weights.mul_(self.p["weight_decay"])
        scores = torch.einsum("bn,bnm->bm", features, self.weights)
        action = torch.stack((scores[:, 0].tanh(), scores[:, 1].sigmoid(), scores[:, 2].sigmoid()), 1)
        self.previous_features = features.detach()
        self.previous_action = action.detach()
        self.previous_energy = energy.detach().clone()
        return action

    def structure(self):
        return {"units": self.n, "connections": self.n * (self.receptors.shape[0] + 3)}
