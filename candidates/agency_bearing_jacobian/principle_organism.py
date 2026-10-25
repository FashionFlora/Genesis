"""Action-conditioned estimate of how turns shift visual bearing."""

import torch


PARAMS = {
    "reafferent_rate": 0.10,
    "reafferent_decay": 0.995,
    "reafferent_gain": 0.62,
    "sensory_gain": 0.58,
    "explore_turn": 0.42,
    "drive": 0.82,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.device = torch.device(device)
        self.batch = int(batch)
        self.n_units = int(n_units)
        self.p = {**PARAMS, **(params or {})}
        self.gen = torch.Generator(device=self.device).manual_seed(int(seed) + 191)
        self.eye_width = max(1, min(16, int(n_sensors) // 3))
        self.turn_state = torch.zeros(self.batch, device=self.device)
        self.reafference = torch.zeros(self.batch, 2, device=self.device)
        self.previous_bearing = torch.zeros(self.batch, device=self.device)
        self.previous_visible = torch.zeros(self.batch, dtype=torch.bool, device=self.device)
        self.age = torch.zeros(self.batch, device=self.device)
        self.phase = torch.rand(self.batch, device=self.device, generator=self.gen) * 6.2831853

    def act(self, sensors):
        x = torch.as_tensor(sensors, device=self.device, dtype=torch.float32)
        eye = x[:, :self.eye_width * 3].reshape(self.batch, self.eye_width, 3).clamp_min(0)
        visual = eye.sum(dim=2)
        angles = torch.arange(self.eye_width, device=self.device, dtype=torch.float32)
        angles = angles * (6.2831853 / float(self.eye_width))
        total = visual.sum(dim=1)
        vx = (visual * angles.cos()).sum(dim=1)
        vy = (visual * angles.sin()).sum(dim=1)
        bearing = torch.atan2(vy, vx)
        visible = total > 0.10

        bearing_change = torch.atan2(
            torch.sin(bearing - self.previous_bearing),
            torch.cos(bearing - self.previous_bearing),
        )
        active = (self.age > 0) & visible & self.previous_visible
        direction = (self.turn_state >= 0).long()
        self.reafference.mul_(self.p["reafferent_decay"])
        rate = self.p["reafferent_rate"]
        for index in (0, 1):
            selected = active & (direction == index)
            estimate = self.reafference[:, index]
            updated = estimate + rate * (bearing_change - estimate)
            self.reafference[:, index] = torch.where(selected, updated, estimate)

        # The action-conditioned bearing shift estimates local turn influence.
        consequence = torch.tanh(2.0 * (self.reafference[:, 0] - self.reafference[:, 1]))
        correction = torch.where(
            visible,
            torch.tanh(1.9 * bearing),
            self.p["explore_turn"] * torch.sin(self.phase + self.age * 0.037),
        )
        turn = self.p["sensory_gain"] * correction - self.p["reafferent_gain"] * consequence
        self.turn_state.copy_(turn.clamp(-1, 1))

        concentration = torch.sqrt(vx.square() + vy.square()) / (total + 1e-5)
        bite = (visible & (total > 1.25) & (concentration > 0.22)).float()
        drive = torch.where(visible, torch.full_like(total, self.p["drive"]),
                            torch.full_like(total, 0.34))
        self.previous_bearing.copy_(bearing)
        self.previous_visible.copy_(visible)
        self.age += 1
        return torch.stack((turn.clamp(-1, 1), drive.clamp(-1, 1), bite), dim=1)

    def structure(self):
        active = (self.turn_state.abs() + self.reafference.abs().sum(dim=1) + 0.01).clamp(0, 1)
        return {
            "units": torch.full((self.batch,), float(self.n_units), device=self.device),
            "connections": active * (self.n_units + self.eye_width * 3),
            "activity": self.previous_bearing,
        }
