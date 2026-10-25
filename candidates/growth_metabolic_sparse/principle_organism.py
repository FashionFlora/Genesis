"""Sparse energy associations scale their credit by metabolic reserve."""

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
        # Each organism owns its local pixel/color slots.  An active mask makes
        # the tensor logically sparse while keeping batch rows independent.
        self.key_index = torch.arange(self.pixels * 3, device=device).expand(batch, -1).clone()
        self.active = torch.zeros(batch, self.pixels * 3, dtype=torch.bool, device=device)
        self.trace = torch.zeros(batch, self.pixels * 3, device=device)
        self.previous_pixel = torch.full((batch,), -1, dtype=torch.long, device=device)
        self.previous_color = torch.zeros(batch, dtype=torch.long, device=device)
        self.previous_value = torch.zeros(batch, device=device)
        self.previous_energy = torch.zeros(batch, device=device)
        self.previous_bite = torch.zeros(batch, device=device)

    def act(self, sensors):
        eye = sensors[:, :self.pixels * 3].reshape(self.batch, self.pixels, 3).clamp_min(0)
        energy = sensors[:, -1].clamp(0, 1)

        outcome = ((energy - self.previous_energy) * self.previous_bite).clamp(-0.1, 0.3)
        self.trace.mul_(self.trace_decay)
        previous_ids = self.previous_pixel * 3 + self.previous_color
        previous_ids = torch.where(self.previous_pixel >= 0, previous_ids, previous_ids.new_full((), -1))
        evidence = ((previous_ids >= 0) & (self.previous_bite > 0.5)
                    & (self.previous_value > 0.0) & (outcome.abs() > 1e-6))
        row = torch.arange(self.batch, device=self.device)
        columns = previous_ids.clamp_min(0)
        # Credit is gated continuously by the reserve present when the sensory
        # choice was made; topology still follows the trace law.
        delta = torch.where(evidence, self.previous_value * outcome * self.previous_energy,
                            torch.zeros_like(outcome))
        self.trace[row, columns] += delta
        self.active[row, columns] |= evidence

        preference = (torch.ones_like(eye).reshape(self.batch, -1)
                      + self.association_gain * self.trace.clamp(-1.0, 1.5) * self.active).reshape(
                          self.batch, self.pixels, 3).clamp_min(0.05)
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
        self.active &= self.trace.abs() > 0.002
        return torch.stack((turn, speed, bite), dim=1)

    def structure(self):
        active = self.active & (self.trace.abs() > 0.002)
        active_links = float(active.sum(dim=1).float().mean().item())
        active_units = float((active.reshape(self.batch, self.pixels, 3).any(dim=2).sum(dim=1).float().mean().item()))
        memory = int(active_links * 12 + self.angles.numel() * 4 + 28)
        return {"units": 2.0 + active_units, "connections": 2.0 + active_links,
                "memory_bytes": memory}
