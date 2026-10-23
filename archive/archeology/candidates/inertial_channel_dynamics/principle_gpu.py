PARAMS = {"adaptation": 0.2}


class SystemGPU:
    def __init__(self, n_units, device, seed=0):
        import torch
        self.device = device
        self.previous = None
        self.inertia = torch.zeros(n_units, dtype=torch.float32, device=device)
        self.pending_delta = torch.zeros_like(self.inertia)
        self.pending_prediction = torch.full_like(self.inertia, 0.5)

    def step(self, observation):
        import torch
        if self.previous is None:
            self.previous = observation.clone()
            return torch.full_like(observation, 0.5)
        error = observation - self.pending_prediction
        self.inertia.add_(PARAMS["adaptation"] * error * self.pending_delta).clamp_(-1.0, 1.0)
        delta = observation - self.previous
        prediction = (observation + self.inertia * delta).clamp(0.0, 1.0)
        self.pending_delta.copy_(delta)
        self.pending_prediction.copy_(prediction)
        self.previous.copy_(observation)
        return prediction

    def structure(self):
        return {"units": self.previous.numel() if self.previous is not None else 0,
                "connections": self.inertia.abs().sum(),
                "memory_bytes": self.inertia.numel() * 16}
