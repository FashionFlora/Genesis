"""Agency as a persistent motor state corrected by current sensation."""

import torch


PARAMS = {
    "action_memory": True,
    "action_persistence": 0.72,
    "sensory_correction": 0.58,
    "explore_turn": 0.42,
    "drive": 0.82,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.device = torch.device(device)
        self.batch = int(batch)
        self.n_units = int(n_units)
        self.p = {**PARAMS, **(params or {})}
        self.gen = torch.Generator(device=self.device).manual_seed(int(seed) + 911)
        self.turn_state = torch.zeros(self.batch, device=self.device)
        self.previous_signal = torch.zeros(self.batch, device=self.device)
        self.age = torch.zeros(self.batch, device=self.device)
        self.phase = torch.rand(self.batch, device=self.device, generator=self.gen) * 6.2831853

    def act(self, sensors):
        x = torch.as_tensor(sensors, device=self.device, dtype=torch.float32)
        eye = x[:, :48].reshape(self.batch, 16, 3).clamp_min(0)
        # The first four pixels carry a context cue in green; suppress it when
        # estimating food bearings. Sensation corrects a persistent motor state.
        food = eye.clone()
        food[:, :4, 1] *= 0.15
        channel_strength = food.mean(dim=1)
        channel = channel_strength.argmax(dim=1)
        chosen = food[torch.arange(self.batch, device=self.device), :, channel]
        angles = torch.arange(16, device=self.device, dtype=torch.float32) * (6.2831853 / 16.0)
        total = chosen.sum(dim=1)
        vx = (chosen * angles.cos()).sum(dim=1)
        vy = (chosen * angles.sin()).sum(dim=1)
        bearing = torch.atan2(vy, vx)
        visible = total > 0.10
        sweep = torch.sin(self.phase + self.age * 0.037)
        correction = torch.where(visible, torch.tanh(1.9 * bearing),
                                 self.p["explore_turn"] * sweep)
        persistence = self.p["action_persistence"]
        memory = persistence * self.turn_state if self.p["action_memory"] else 0.0
        turn = memory + (1.0 - persistence) * correction * self.p["sensory_correction"]
        self.turn_state.copy_(turn.clamp(-1, 1))
        concentration = torch.sqrt(vx.square() + vy.square()) / (total + 1e-5)
        # Bite only on a concentrated, strong signal; after a bite, regrowth
        # and the next energy jump provide the endogenous teaching event.
        bite = (visible & (total > 1.25) & (concentration > 0.22)).float()
        drive = torch.where(visible, torch.full_like(total, self.p["drive"]),
                            torch.full_like(total, 0.34))
        self.previous_signal.copy_(total)
        self.age += 1
        return torch.stack((turn.clamp(-1, 1), drive.clamp(-1, 1), bite), dim=1)

    def structure(self):
        active = (self.turn_state.abs() + 0.01).clamp(0, 1)
        return {"units": torch.full((self.batch,), float(self.n_units), device=self.device),
                "connections": active * (self.n_units + 48 * 3),
                "activity": self.previous_signal}
