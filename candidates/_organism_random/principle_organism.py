PARAMS = {"mode": "random", "rate": 0.015, "decay": 0.985, "explore": 0.15}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        import torch
        self.torch, self.n, self.batch, self.device = torch, n_units, batch, device
        self.energy_index = n_sensors - 1
        self.p = {**PARAMS, **(params or {})}
        self.gen = torch.Generator(device=device).manual_seed(seed)
        self.mode = self.p["mode"]
        self.prev_energy = torch.zeros(batch, device=device)
        if self.mode == "delta":
            self.input = torch.randn(n_sensors, n_units, device=device, generator=self.gen) / n_sensors ** .5
            self.readout = torch.randn(batch, n_units, n_motors, device=device, generator=self.gen) * n_units ** -.5
            self.trace = torch.zeros(batch, n_units, device=device)
            self.prev_action = torch.zeros(batch, device=device)
        self.tick = 0

    def act(self, sensors):
        torch = self.torch
        self.tick += 1
        if self.mode == "random":
            return torch.cat((torch.rand(self.batch, 1, device=self.device, generator=self.gen) * 2 - 1,
                              torch.rand(self.batch, 2, device=self.device, generator=self.gen)), 1)
        if self.mode == "braitenberg":
            turn = sensors[:, 1] - sensors[:, 2]
            return torch.stack((turn, sensors[:, 0], torch.ones_like(turn)), 1).clamp(-1, 1)
        x = torch.tanh(sensors @ self.input)
        if self.tick > 1:
            energy_delta = sensors[:, self.energy_index] - self.prev_energy
            self.readout[:, :, 0] += (self.p["rate"] * energy_delta * self.prev_action)[:, None] * self.trace
            self.readout.mul_(self.p["decay"])
        out = torch.einsum("bn,bnm->bm", x, self.readout)
        self.prev_energy = sensors[:, self.energy_index].clone()
        self.prev_action = out[:, 0].tanh().detach()
        self.trace.mul_(self.p["decay"]).add_(x)
        return torch.tanh(out)

    def structure(self):
        if self.mode == "delta":
            return {"units": self.n, "connections": self.n * 22}
        return {"units": self.n, "connections": 0}
