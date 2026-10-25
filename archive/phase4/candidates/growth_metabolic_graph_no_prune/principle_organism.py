"""No-pruning ablation of the sparse sensory association graph."""

import math

import torch


PARAMS = {
    "learning_rate": 0.8,
    "decay": 0.997,
    "use_decay": 0.985,
    "prune_use": -1.0,
    "prune_weight": -1.0,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.torch = torch
        self.batch = batch
        self.device = device
        self.pixels = (n_sensors - 1) // 3
        self.angles = torch.arange(self.pixels, device=device) * (2 * math.pi / self.pixels)
        self.params = {**PARAMS, **(params or {})}
        self.keys = []
        self.key_to_index = {}
        self.colors = torch.empty(0, dtype=torch.long, device=device)
        self.weights = torch.zeros(batch, 0, device=device)
        self.use = torch.zeros_like(self.weights)
        self.exists = torch.zeros(batch, 0, dtype=torch.bool, device=device)
        self.previous_active = torch.zeros_like(self.weights)
        self.previous_color = torch.zeros(batch, dtype=torch.long, device=device)
        self.previous_bite = torch.zeros(batch, dtype=torch.bool, device=device)
        self.previous_energy = torch.zeros(batch, device=device)
        self.initialized = False

    def _grow(self, eye):
        observed = (eye > 0.08).any(dim=0).nonzero(as_tuple=False).tolist()
        new_keys = []
        new_colors = []
        for pixel, color in observed:
            key = color * self.pixels + pixel
            if key not in self.key_to_index:
                self.key_to_index[key] = len(self.keys)
                self.keys.append(key)
                new_keys.append(key)
                new_colors.append(color)
        if not new_keys:
            return
        count = len(new_keys)
        self.colors = torch.cat((self.colors, torch.tensor(new_colors, device=self.device)))
        self.weights = torch.cat((self.weights, self.weights.new_zeros(self.batch, count)), dim=1)
        self.use = torch.cat((self.use, self.use.new_zeros(self.batch, count)), dim=1)
        self.exists = torch.cat((self.exists, self.exists.new_zeros(self.batch, count)), dim=1)
        self.previous_active = torch.cat(
            (self.previous_active, self.previous_active.new_zeros(self.batch, count)), dim=1)

    def _compact(self):
        keep = self.exists.any(dim=0)
        if keep.numel() and not bool(keep.all()):
            kept_indices = keep.nonzero(as_tuple=False).flatten().tolist()
            self.keys = [self.keys[index] for index in kept_indices]
            self.key_to_index = {key: index for index, key in enumerate(self.keys)}
            self.colors = self.colors[keep]
            self.weights = self.weights[:, keep]
            self.use = self.use[:, keep]
            self.exists = self.exists[:, keep]
            self.previous_active = self.previous_active[:, keep]

    def act(self, sensors):
        eye = sensors[:, :self.pixels * 3].reshape(self.batch, self.pixels, 3)
        energy = sensors[:, -1]
        self._grow(eye)

        if self.keys:
            values = torch.stack([eye[:, key % self.pixels, key // self.pixels]
                                  for key in self.keys], dim=1)
            active = values > 0.08
            self.weights.mul_(self.params["decay"])
            self.use.mul_(self.params["use_decay"])
            if self.initialized:
                gain = (energy - self.previous_energy).clamp(-0.05, 0.2)
                gain = gain * self.previous_bite.float() * self.params["learning_rate"]
                matches = self.previous_color[:, None] == self.colors[None, :]
                self.weights.add_(self.previous_active * matches * gain[:, None])
            self.exists |= active
            self.use.add_(values * active).clamp_(max=1.0)
            stale = self.exists & (self.use < self.params["prune_use"])
            stale &= self.weights.abs() < self.params["prune_weight"]
            self.exists &= ~stale
            self.weights.mul_(self.exists)
            self.use.mul_(self.exists)

            evidence = eye.sum(dim=1)
            confidence = self.weights.abs().sum(dim=1) > 1e-3
            color_scores = torch.stack([
                (self.weights * self.exists * (self.colors[None, :] == color)).sum(dim=1)
                for color in range(3)
            ], dim=1)
            scores = torch.where(confidence[:, None], color_scores, evidence)
            color = scores.argmax(dim=1)
            selected = eye.gather(2, color[:, None, None].expand(-1, self.pixels, 1))[:, :, 0]
            turn = torch.atan2((selected * self.angles.sin()[None]).sum(dim=1),
                               (selected * self.angles.cos()[None]).sum(dim=1)) / math.pi
            bite = selected.max(dim=1).values > 0.08
            self.previous_active = values * active
            self._compact()
        else:
            evidence = eye.sum(dim=1)
            color = evidence.argmax(dim=1)
            selected = eye.gather(2, color[:, None, None].expand(-1, self.pixels, 1))[:, :, 0]
            turn = torch.atan2((selected * self.angles.sin()[None]).sum(dim=1),
                               (selected * self.angles.cos()[None]).sum(dim=1)) / math.pi
            bite = selected.max(dim=1).values > 0.08

        self.previous_color.copy_(color)
        self.previous_bite.copy_(bite)
        self.previous_energy.copy_(energy)
        self.initialized = True
        return torch.stack((turn, torch.full_like(turn, 0.72), bite.float()), dim=1)

    def structure(self):
        units = self.exists.sum(dim=1)
        return {"units": units, "connections": units}
