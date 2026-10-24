"""A homeostatic oscillator: local activity traces are selected by energy flow."""
import torch


PARAMS = {
    "rate": 0.035,
    "trace_decay": 0.965,
    "state_decay": 0.82,
    "weight_decay": 0.9995,
    "drive": 0.32,
    "homeostasis": 0.04,
    "speed_energy_gain": 7.0,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.device = torch.device(device)
        self.batch = batch
        self.p = {**PARAMS, **(params or {})}
        self.n = n_units
        self.width = min(n_units, 96)
        gen = torch.Generator(device=device).manual_seed(seed)
        self.receptors = torch.randn(n_sensors + 2, self.width, device=device, generator=gen) / (n_sensors + 2)**0.5
        self.readout = torch.randn(batch, self.width, n_motors, device=device, generator=gen) / self.width**0.5
        self.state = torch.zeros(batch, self.width, device=device)
        self.trace = torch.zeros(batch, self.width, device=device)
        self.prev_state = None
        self.prev_action = torch.zeros(batch, n_motors, device=device)
        self.prev_energy = torch.zeros(batch, device=device)
        self.prev_color = torch.zeros(batch, 3, device=device)
        self.food_value = torch.full((batch, 3), 0.01, device=device)
        self.phase = torch.zeros(batch, device=device)
        self.angles = torch.arange(16, device=device) * (2 * torch.pi / 16)
        self.energy_sensor = n_sensors > 48

    def act(self, sensors):
        x = sensors.detach()
        energy = x[:, -1] if self.energy_sensor else torch.zeros(self.batch, device=self.device)
        eye = x[:, :48].reshape(self.batch, 16, 3).sum(2)
        color = x[:, :48].reshape(self.batch, 16, 3).sum(1)
        moment = torch.stack(((eye * self.angles.sin()).sum(1),
                              (eye * self.angles.cos()).sum(1)), 1)
        drive = torch.cat((x, moment), 1)
        incoming = drive @ self.receptors
        self.phase = self.phase + 0.11 + 0.08 * (energy - 0.5)
        oscillation = self.phase.sin()[:, None] * self.p["drive"]
        self.state = torch.tanh(self.p["state_decay"] * self.state + incoming + oscillation)
        if self.prev_state is not None:
            delta = energy - self.prev_energy
            self.trace.mul_(self.p["trace_decay"]).add_(self.prev_state)
            three_factor = (self.p["rate"] * delta)[:, None, None]
            self.readout.add_(three_factor * self.trace[:, :, None] * self.prev_action[:, None, :])
            self.readout.mul_(self.p["weight_decay"])
            self.food_value.add_(self.p["rate"] * (delta + 0.001)[:, None] * self.prev_color)
        scores = torch.einsum("bn,bnm->bm", self.state, self.readout)
        turn = (eye * self.angles.sin()).sum(1)
        near = eye.amax(1)
        color_score = (color * self.food_value).sum(1) / color.sum(1).clamp_min(1e-4)
        bite = 2.0 * (near - 2.3) + 6.0 * color_score
        speed = torch.sigmoid(self.p["speed_energy_gain"] * (energy - 0.5))
        motors = torch.stack((0.35 * turn + 0.02 * scores[:, 0], speed, bite), 1)
        action = torch.stack((motors[:, 0].tanh(), motors[:, 1].sigmoid(), motors[:, 2].sigmoid()), 1)
        self.prev_state = self.state.detach()
        self.prev_action = action.detach()
        self.prev_energy = energy.detach()
        self.prev_color = color.detach()
        return action

    def structure(self):
        return {"units": self.n, "connections": self.width * (self.width + 3),
                "memory_bytes": self.state.numel() * 4 + self.readout.numel() * 4}
