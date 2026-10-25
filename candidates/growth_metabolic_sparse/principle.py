"""Pixel-local energy eligibility links grow through experience and fade unused."""

import math

import torch


PARAMS = {
    "trace_decay": 0.985,
    "association_gain": 0.8,
    "speed": 0.6,
    "bite_threshold": 0.08,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        chosen = {**PARAMS, **(params or {})}
        self.batch = batch
        self.device = device
        self.pixels = (n_sensors - 1) // 3
        self.angles = torch.arange(self.pixels, device=device) * (2 * math.pi / self.pixels)
        self.trace_decay = chosen["trace_decay"]
        self.association_gain = chosen["association_gain"]
        self.speed = chosen["speed"]
        self.bite_threshold = chosen["bite_threshold"]
        # Persistent associations use columns allocated only after a selected
        # pixel/color pair has produced an energy outcome.  The dense preference
        # image below is transient and is not part of the learned structure.
        self.keys = []
        self.key_index = torch.full((self.pixels * 3,), -1, dtype=torch.long, device=device)
        self.trace = torch.empty(batch, 0, device=device)
        self.previous_pixel = torch.full((batch,), -1, dtype=torch.long, device=device)
        self.previous_color = torch.zeros(batch, dtype=torch.long, device=device)
        self.previous_value = torch.zeros(batch, device=device)
        self.previous_energy = torch.zeros(batch, device=device)
        self.previous_bite = torch.zeros(batch, device=device)

    def _ensure_keys(self, ids):
        valid = ids >= 0
        if not bool(valid.any()):
            return
        known = self.key_index[ids.clamp_min(0)]
        missing = torch.unique(ids[valid & (known < 0)]).tolist()
        if not missing:
            return
        old = len(self.keys)
        self.keys.extend((int(item // 3), int(item % 3)) for item in missing)
        added = torch.zeros(self.batch, len(missing), device=self.device)
        self.trace = torch.cat((self.trace, added), dim=1)
        self.key_index[torch.as_tensor(missing, device=self.device)] = torch.arange(
            old, old + len(missing), device=self.device)

    def act(self, sensors):
        eye = sensors[:, :self.pixels * 3].reshape(self.batch, self.pixels, 3).clamp_min(0)
        energy = sensors[:, -1].clamp(0, 1)

        outcome = ((energy - self.previous_energy) * self.previous_bite).clamp(-0.1, 0.3)
        if self.trace.shape[1]:
            self.trace.mul_(self.trace_decay)
        previous_ids = self.previous_pixel * 3 + self.previous_color
        previous_ids = torch.where(self.previous_pixel >= 0, previous_ids, previous_ids.new_full((), -1))
        evidence = ((previous_ids >= 0) & (self.previous_bite > 0.5)
                    & (self.previous_value > 0.0) & (outcome.abs() > 1e-6))
        self._ensure_keys(torch.where(evidence, previous_ids, previous_ids.new_full((), -1)))
        if self.trace.shape[1]:
            row = torch.arange(self.batch, device=self.device)
            columns = self.key_index[previous_ids.clamp_min(0)]
            delta = torch.where(evidence, self.previous_value * outcome,
                                torch.zeros_like(outcome))
            self.trace.index_put_((row, columns.clamp_min(0)), delta, accumulate=True)

        if self.trace.shape[1]:
            ids = torch.as_tensor([pixel * 3 + color for pixel, color in self.keys],
                                  device=self.device, dtype=torch.long)
            preference = torch.ones_like(eye).reshape(self.batch, -1)
            preference.scatter_add_(1, ids.expand(self.batch, -1),
                                    self.association_gain * self.trace.clamp(-1.0, 1.5))
            preference = preference.reshape(self.batch, self.pixels, 3).clamp_min(0.05)
        else:
            preference = torch.ones_like(eye)
        color = (eye * preference).sum(dim=1).argmax(dim=1)
        selected_eye = eye.gather(2, color[:, None, None].expand(-1, self.pixels, 1))[:, :, 0]
        selected_preference = preference.gather(
            2, color[:, None, None].expand(-1, self.pixels, 1))[:, :, 0]
        weighted_eye = selected_eye * selected_preference
        x = (weighted_eye * self.angles.cos()).sum(dim=1)
        y = (weighted_eye * self.angles.sin()).sum(dim=1)
        turn = torch.atan2(y, x) / math.pi
        speed = self.speed * (energy > 0.15)
        bite = (weighted_eye.max(dim=1).values > self.bite_threshold).float()

        self.previous_pixel.copy_(weighted_eye.argmax(dim=1))
        self.previous_color.copy_(color)
        rows = torch.arange(self.batch, device=self.device)
        self.previous_value.copy_(eye[rows, self.previous_pixel, color])
        self.previous_energy.copy_(energy)
        self.previous_bite.copy_(bite)
        if self.trace.shape[1]:
            keep = self.trace.abs().amax(dim=0) > 0.002
            if not bool(keep.all()):
                self.trace = self.trace[:, keep]
                self.keys = [key for key, active in zip(self.keys, keep.tolist()) if active]
                self.key_index.fill_(-1)
                if self.keys:
                    ids = torch.as_tensor([pixel * 3 + color for pixel, color in self.keys], device=self.device)
                    self.key_index[ids] = torch.arange(len(self.keys), device=self.device)
        return torch.stack((turn, speed, bite), dim=1)

    def structure(self):
        active = self.trace.abs() > 0.002
        active_links = float(active.sum(dim=1).float().mean().item())
        active_units = float(len({pixel for pixel, _ in self.keys}))
        memory = int(self.trace.shape[1] * 4 + len(self.keys) * 8
                     + self.key_index.numel() * 8 + self.angles.numel() * 4 + 28)
        return {"units": 2.0 + active_units, "connections": 2.0 + active_links,
                "memory_bytes": memory}
