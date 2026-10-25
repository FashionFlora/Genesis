"""Action-conditioned prediction of the next visual change."""

import torch


PARAMS = {
    "prediction_rate": 0.08,
    "prediction_decay": 0.995,
    "prediction_gain": 0.72,
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
        self.gen = torch.Generator(device=self.device).manual_seed(int(seed) + 911)
        self.eye_width = max(1, min(16, int(n_sensors) // 3))
        self.turn_state = torch.zeros(self.batch, device=self.device)
        self.previous_signal = torch.zeros(self.batch, device=self.device)
        self.predicted_delta = torch.zeros(self.batch, 2, device=self.device)
        self.age = torch.zeros(self.batch, device=self.device)
        self.phase = torch.rand(self.batch, device=self.device, generator=self.gen) * 6.2831853

    def act(self, sensors):
        x = torch.as_tensor(sensors, device=self.device, dtype=torch.float32)
        eye = x[:, :self.eye_width * 3].reshape(self.batch, self.eye_width, 3).clamp_min(0)
        channel_strength = eye.mean(dim=1)
        channel = channel_strength.argmax(dim=1)
        chosen = eye[torch.arange(self.batch, device=self.device), :, channel]
        angles = torch.arange(self.eye_width, device=self.device, dtype=torch.float32)
        angles = angles * (6.2831853 / float(self.eye_width))
        total = chosen.sum(dim=1)
        vx = (chosen * angles.cos()).sum(dim=1)
        vy = (chosen * angles.sin()).sum(dim=1)
        bearing = torch.atan2(vy, vx)
        visible = total > 0.10

        # Credit only the sensory change that followed the previous motor command.
        # The two entries are predictions for positive and negative turns.
        change = total - self.previous_signal
        active = self.age > 0
        direction = (self.turn_state >= 0).long()
        rate = self.p["prediction_rate"]
        decay = self.p["prediction_decay"]
        self.predicted_delta.mul_(decay)
        for index in (0, 1):
            selected = active & (direction == index)
            estimate = self.predicted_delta[:, index]
            self.predicted_delta[:, index] = torch.where(
                selected, estimate + rate * (change - estimate), estimate)
        advantage = torch.tanh(3.0 * (self.predicted_delta[:, 0] - self.predicted_delta[:, 1]))

        correction = torch.where(visible, torch.tanh(1.9 * bearing),
                                self.p["explore_turn"] * torch.sin(self.phase + self.age * 0.037))
        turn = correction * self.p["sensory_gain"] + self.p["prediction_gain"] * advantage
        self.turn_state.copy_(turn.clamp(-1, 1))
        concentration = torch.sqrt(vx.square() + vy.square()) / (total + 1e-5)
        bite = (visible & (total > 1.25) & (concentration > 0.22)).float()
        drive = torch.where(visible, torch.full_like(total, self.p["drive"]),
                            torch.full_like(total, 0.34))
        self.previous_signal.copy_(total)
        self.age += 1
        return torch.stack((turn.clamp(-1, 1), drive.clamp(-1, 1), bite), dim=1)

    def structure(self):
        active = (self.turn_state.abs() + self.predicted_delta.abs().sum(dim=1) + 0.01).clamp(0, 1)
        return {"units": torch.full((self.batch,), float(self.n_units), device=self.device),
                "connections": active * (self.n_units + self.eye_width * 3),
                "activity": self.previous_signal}
