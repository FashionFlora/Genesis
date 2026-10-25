"""Local causal traces grow on evidence and expire when unsupported."""

import math

import torch


PARAMS = {
    "decay": 0.997,
    "use_decay": 0.985,
    "scarcity_prune": 2.0,
    "prune_use": 0.025,
    "prune_weight": 0.002,
    "trace_deposit": 4.0,
    "loss_deposit": 2.0,
    "loss_gate": 0.005,
    "evidence_gain": 0.25,
    "bite_threshold": 0.08,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.batch = batch
        self.device = device
        self.has_energy = n_sensors % 3 == 1
        self.pixels = (n_sensors - int(self.has_energy)) // 3
        self.angles = torch.arange(self.pixels, device=device) * (2 * math.pi / self.pixels)
        self.params = {**PARAMS, **(params or {})}
        self.keys = []
        self.key_to_index = {}
        self.colors = torch.empty(0, dtype=torch.long, device=device)
        self.trace = torch.zeros(batch, 0, device=device)
        self.use = torch.zeros_like(self.trace)
        self.exists = torch.zeros(batch, 0, dtype=torch.bool, device=device)
        self.previous_active = torch.zeros_like(self.trace)
        self.previous_color = torch.zeros(batch, dtype=torch.long, device=device)
        self.previous_bite = torch.zeros(batch, device=device)
        self.previous_energy = torch.full((batch,), 0.5, device=device)
        self.initialized = False

    def _grow(self, eye):
        observed = (eye > self.params["bite_threshold"]).any(dim=0).nonzero().tolist()
        new = [(color * self.pixels + pixel, color) for pixel, color in observed
               if color * self.pixels + pixel not in self.key_to_index]
        if not new:
            return
        for key, _ in new:
            self.key_to_index[key] = len(self.keys)
            self.keys.append(key)
        count = len(new)
        self.colors = torch.cat((self.colors, torch.tensor([c for _, c in new], device=self.device)))
        self.trace = torch.cat((self.trace, self.trace.new_zeros(self.batch, count)), dim=1)
        self.use = torch.cat((self.use, self.use.new_zeros(self.batch, count)), dim=1)
        self.exists = torch.cat((self.exists, self.exists.new_zeros(self.batch, count)), dim=1)
        self.previous_active = torch.cat(
            (self.previous_active, self.previous_active.new_zeros(self.batch, count)), dim=1)

    def _compact(self):
        keep = self.exists.any(dim=0)
        if keep.numel() and not bool(keep.all()):
            indices = keep.nonzero().flatten().tolist()
            self.keys = [self.keys[i] for i in indices]
            self.key_to_index = {key: i for i, key in enumerate(self.keys)}
            self.colors = self.colors[keep]
            self.trace = self.trace[:, keep]
            self.use = self.use[:, keep]
            self.exists = self.exists[:, keep]
            self.previous_active = self.previous_active[:, keep]

    def act(self, sensors):
        eye = sensors[:, :self.pixels * 3].reshape(self.batch, self.pixels, 3)
        energy = (sensors[:, -1].clamp(0, 1) if self.has_energy
                  else torch.full_like(self.previous_energy, 0.5))
        self._grow(eye)

        if self.keys:
            values = torch.stack([eye[:, key % self.pixels, key // self.pixels]
                                  for key in self.keys], dim=1)
            active = values > self.params["bite_threshold"]
            self.trace.mul_(self.params["decay"])
            self.use.mul_(self.params["use_decay"] **
                          (1 + self.params["scarcity_prune"] * (1 - energy[:, None])))
            if self.initialized:
                delta = energy - self.previous_energy
                gain = torch.where(delta > self.params["loss_gate"],
                                   delta * self.params["trace_deposit"],
                                   torch.where(delta < -self.params["loss_gate"],
                                               delta * self.params["loss_deposit"],
                                               torch.zeros_like(delta))) * self.previous_bite
                eligible = self.previous_active * (self.previous_color[:, None] == self.colors[None, :])
                self.trace.add_(eligible * gain[:, None])
            self.exists |= active
            self.use.add_(values * active).clamp_(max=1.0)
            stale = self.exists & (self.use < self.params["prune_use"])
            stale &= self.trace.abs() < self.params["prune_weight"]
            self.exists &= ~stale
            self.trace.mul_(self.exists)
            self.use.mul_(self.exists)
            scores = torch.stack([
                (self.trace * self.exists * (self.colors[None, :] == color)).sum(dim=1)
                for color in range(3)
            ], dim=1)
            color = (energy[:, None] * scores
                     + self.params["evidence_gain"] * (1 - energy[:, None]) * eye.sum(dim=1)).argmax(1)
            self.previous_active = values * active
            self._compact()
        else:
            color = eye.sum(dim=1).argmax(dim=1)

        selected = eye.gather(2, color[:, None, None].expand(-1, self.pixels, 1))[:, :, 0]
        turn = torch.atan2((selected * self.angles.sin()[None]).sum(dim=1),
                           (selected * self.angles.cos()[None]).sum(dim=1)) / math.pi
        bite = (selected.max(dim=1).values > self.params["bite_threshold"]).float()
        self.previous_color.copy_(color)
        self.previous_bite.copy_(bite)
        self.previous_energy.copy_(energy)
        self.initialized = True
        return torch.stack((turn, torch.full_like(energy, 0.575), bite), dim=1)

    def structure(self):
        units = self.exists.sum(dim=1)
        return {"units": units, "connections": units}
