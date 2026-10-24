"""Demand-grown predictive niches with local whole-action energy credit."""
import torch

PARAMS = {"novelty": 0.02, "decay": 0.994, "learn": 0.08,
          "competition": 0.001, "credit": 0.08}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.torch = torch
        self.device = torch.device(device)
        self.batch = batch
        self.n_sensors = n_sensors
        self.max_units = n_units
        self.capacity = min(n_units, 1)
        self.p = {**PARAMS, **(params or {})}
        self.centers = torch.zeros(batch, self.capacity, n_sensors, device=device)
        self.utility = torch.zeros(batch, self.capacity, device=device)
        self.active = torch.zeros(batch, self.capacity, dtype=torch.bool, device=device)
        self.actions = torch.zeros(batch, self.capacity, 3, device=device)
        self.previous_action = None
        self.previous_energy = None
        self.rng = torch.Generator(device=device).manual_seed(seed)

    def act(self, sensors):
        torch = self.torch
        x = sensors.detach()
        if self.previous_action is not None and self.n_sensors > 48:
            delta = x[:, -1] - self.previous_energy
            self.actions += (self.p["credit"] * delta.sign()[:, None, None]
                             * self.previous_action[:, None, :]
                             * self.active[:, :, None])

        dist = (self.centers - x[:, None, :]).square().mean(-1)
        dist = torch.where(self.active, dist, torch.full_like(dist, float("inf")))
        nearest_dist, nearest = dist.min(1)
        empty = ~self.active.any(1)
        novel = empty | (nearest_dist > self.p["novelty"])
        self.last_prediction_error = torch.where(empty, torch.zeros_like(nearest_dist), nearest_dist)

        self.utility.mul_(self.p["decay"])
        if bool(novel.any()):
            rows = torch.where(novel)[0]
            can_add = ~self.active[rows].all(1)
            if not bool(can_add.any()) and self.capacity < self.max_units:
                new_capacity = min(self.max_units, max(self.capacity + 1, self.capacity * 2))
                extra = new_capacity - self.capacity
                self.centers = torch.cat((self.centers, self.centers.new_zeros(self.batch, extra, self.n_sensors)), 1)
                self.utility = torch.cat((self.utility, self.utility.new_zeros(self.batch, extra)), 1)
                self.active = torch.cat((self.active, self.active.new_zeros(self.batch, extra)), 1)
                self.actions = torch.cat((self.actions, self.actions.new_zeros(self.batch, extra, 3)), 1)
                self.capacity = new_capacity
                can_add = ~self.active[rows].all(1)
            rows = rows[can_add]
            slots = (~self.active[rows]).float().argmax(1)
            if rows.numel():
                self.active[rows, slots] = True
                self.centers[rows, slots] = x[rows]
                self.utility[rows, slots] = 1.0
                self.actions[rows, slots] = torch.randn(rows.numel(), 3, device=self.device, generator=self.rng) * 0.05
                nearest[rows] = slots

        rows = torch.arange(self.batch, device=self.device)
        idx = nearest
        self.centers[rows, idx] = torch.lerp(self.centers[rows, idx], x, self.p["learn"])
        self.utility[rows, idx] += 1.0
        strongest = self.utility.masked_fill(~self.active, 0).amax(1, keepdim=True)
        self.active &= self.utility >= strongest * self.p["competition"]

        active_actions = self.actions[rows, idx]
        eye = x[:, :48].reshape(self.batch, 16, 3).sum(2)
        left_right = (eye * torch.sin(torch.arange(16, device=self.device) * (2 * torch.pi / 16))).sum(1)
        motors = active_actions.clone()
        motors[:, 0] += left_right.tanh() * 0.35
        motors[:, 1] += 0.35
        motors[:, 2] += 0.15
        self.previous_action = motors.detach()
        self.previous_energy = x[:, -1].clone() if self.n_sensors > 48 else None
        return motors.tanh()

    def structure(self):
        units = int(self.active.sum(1).float().mean().item())
        return {"units": units, "connections": units * 3,
                "allocated_units": self.capacity}
