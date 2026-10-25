"""Metabolic trace controller: action is shaped by sensed energy changes."""

import torch

PARAMS = {"memory_gain": 0.55}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.device = torch.device(device)
        self.batch = int(batch)
        self.n_sensors = int(n_sensors)
        self.n_units = int(n_units)
        self.gen = torch.Generator(device=self.device).manual_seed(int(seed) + 17)
        self.prev_energy = torch.full((batch,), 0.95, device=self.device)
        self.logits = torch.zeros(batch, 3, device=self.device)
        self.last_channel = torch.zeros(batch, dtype=torch.long, device=self.device)
        self.last_signal = torch.zeros(batch, device=self.device)
        self.age = torch.zeros(batch, device=self.device)
        self.quiet = torch.zeros(batch, device=self.device)
        self.phase = torch.rand((batch,), device=self.device, generator=self.gen) * 6.2831853
        self.params = {**PARAMS, **(params or {})}

    def act(self, sensors):
        x = torch.as_tensor(sensors, device=self.device, dtype=torch.float32)
        eye = x[:, :48].reshape(self.batch, 16, 3)
        energy = x[:, 48] if x.shape[1] > 48 else self.prev_energy

        # A positive energy jump is the only teaching signal: it credits the
        # colour that was being pursued on the preceding action.
        delta = energy - self.prev_energy
        gain = delta > 0.08
        loss = delta < -0.012
        rows = torch.arange(self.batch, device=self.device)
        self.logits[rows, self.last_channel] += gain.float() * float(self.params["memory_gain"])
        self.logits *= torch.where(loss[:, None], torch.full_like(self.logits, 0.985),
                                   torch.full_like(self.logits, 0.998))
        self.quiet = torch.where(gain, torch.zeros_like(self.quiet), self.quiet + 1)
        stale = self.quiet > 96
        self.logits = torch.where(stale[:, None], self.logits * 0.85, self.logits)
        self.quiet = torch.where(stale, torch.zeros_like(self.quiet), self.quiet)

        # Circular population vector gives a bearing without an explicit map.
        angles = torch.arange(16, device=self.device, dtype=torch.float32) * (6.2831853 / 16.0)
        cs, sn = angles.cos(), angles.sin()
        strength = eye.clamp_min(0).sum(dim=1)
        visual = eye.clamp_min(0).mean(dim=1)
        score = visual + self.logits * 0.18
        channel = score.argmax(dim=1)
        # Keep the red channel available for food, but suppress isolated
        # looming red signals when another food colour is present.
        other = visual[:, 1:].amax(dim=1)
        red_threat = (channel == 0) & (visual[:, 0] > other * 1.7) & (visual[:, 0] > 0.15)
        channel = torch.where(red_threat, visual[:, 1:].argmax(dim=1) + 1, channel)
        self.last_channel = channel
        chosen = eye[rows, :, channel]
        total = chosen.sum(dim=1)
        vx = (chosen * cs).sum(dim=1)
        vy = (chosen * sn).sum(dim=1)
        bearing = torch.atan2(vy, vx)
        visible = total > 0.045

        # Turn toward the selected signal.  When the eye is empty, metabolism
        # pays for a slow phase sweep that eventually discovers a patch.
        sweep = torch.sin(self.phase + self.age * 0.035)
        turn = torch.where(visible, torch.tanh(2.4 * bearing), 0.42 * sweep)
        concentration = (vx.square() + vy.square()).sqrt() / (total + 1e-5)
        drive = torch.where(visible, (total * 1.8).clamp(0, 0.8), torch.zeros_like(total))
        bite = (visible & (concentration > 0.34) & (total > 0.22)).float()
        # A brief bite pulse avoids repeatedly paying for a wrong patch while
        # retaining pressure to harvest a newly regrown patch.
        bite = bite * ((self.age.remainder(5) < 1).float())

        self.prev_energy = energy
        self.age += 1
        self.last_signal = total
        return torch.stack((turn.clamp(-1, 1), drive.clamp(-1, 1), bite), dim=1)

    def structure(self):
        return {"mass": float(self.n_units), "activity": float(self.last_signal.mean().item())}
