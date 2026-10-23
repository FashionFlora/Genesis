PARAMS = {"rate": 0.04, "decay": 0.999}


class SystemGPU:
    def __init__(self, n_units, device, seed=0):
        import torch
        self.device = device
        self.rate = PARAMS["rate"]
        self.decay = PARAMS["decay"]
        self.bias = torch.full((n_units,), 0.5, device=device)
        self.trace = torch.zeros(n_units, device=device)
        self.mass = torch.zeros(n_units, device=device)

    def step(self, observation):
        import torch
        prediction = (self.bias + self.trace * (observation - 0.5)).clamp(0.01, 0.99)
        self.trace.mul_(self.decay).add_(observation - 0.5)
        self.bias.add_(self.rate * (observation - self.bias)).clamp_(0.01, 0.99)
        self.mass.mul_(self.decay).add_(torch.abs(observation - prediction))
        return prediction

    def structure(self):
        return {"mass": self.mass.mean()}
