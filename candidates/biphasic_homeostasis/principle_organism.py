"""Activity-dependent synaptic scaling with low-activity structural compensation."""

import math

import torch


PARAMS = {
    "learning_rate": 0.8,
    "weight_decay": 0.997,
    "activity_decay": 0.985,
    "activity_target": 0.12,
    "scaling_rate": 0.04,
    "growth_rate": 0.02,
    "prune_rate": 0.01,
    "use_decay": 0.985,
}


class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.torch = torch
        self.batch = batch
        self.device = device
        self.pixels = (n_sensors - 1) // 3
        self.angles = torch.arange(self.pixels, device=device) * (2 * math.pi / self.pixels)
        self.params = {**PARAMS, **(params or {})}
        self.nodes = [dict() for _ in range(batch)]
        self.previous_active = [[] for _ in range(batch)]
        self.previous_color = [0] * batch
        self.previous_bite = [False] * batch
        self.previous_energy = [0.0] * batch
        self.activity = [0.0] * batch
        self.initialized = [False] * batch
        self.node_count = 0

    def act(self, sensors):
        eyes = sensors[:, :self.pixels * 3].reshape(self.batch, self.pixels, 3).detach().tolist()
        energy = sensors[:, -1].detach().tolist()
        turns, bites = [], []
        for row in range(self.batch):
            nodes = self.nodes[row]
            if self.initialized[row]:
                p = self.params
                delta = energy[row] - self.previous_energy[row]
                if self.previous_bite[row]:
                    for key, value in self.previous_active[row]:
                        if key // self.pixels == self.previous_color[row] and key in nodes:
                            nodes[key][0] += p["learning_rate"] * max(-0.05, min(0.2, delta)) * value
                activity_error = self.activity[row] - p["activity_target"]
                scale = max(0.0, 1.0 - p["scaling_rate"] * activity_error)
                for state in nodes.values():
                    state[0] = state[0] * p["weight_decay"] * scale
                    state[1] *= p["use_decay"]

            active = []
            evidence = [0.0, 0.0, 0.0]
            for pixel, rgb in enumerate(eyes[row]):
                for color, value in enumerate(rgb):
                    if value > 0.08:
                        key = color * self.pixels + pixel
                        state = nodes.get(key)
                        if state is None:
                            state = [0.0, 0.0]
                            nodes[key] = state
                        state[1] = min(1.0, state[1] + value)
                        active.append((key, value))
                        evidence[color] += value

            self.activity[row] = (self.params["activity_decay"] * self.activity[row]
                                  + (1.0 - self.params["activity_decay"]) * len(active) / (self.pixels * 3))
            # Low activity recruits weak sensory edges; persistent inactive edges are pruned.
            if self.activity[row] < self.params["activity_target"]:
                for key, value in active:
                    nodes[key][0] += self.params["growth_rate"] * value
            stale = [key for key, (weight, use) in nodes.items()
                     if use < self.params["activity_target"] * 0.2 and abs(weight) < self.params["prune_rate"]]
            for key in stale:
                del nodes[key]

            scores = [0.0, 0.0, 0.0]
            for key, (weight, _) in nodes.items():
                scores[key // self.pixels] += weight
            if not any(abs(value) > 1e-3 for value in scores):
                scores = evidence
            color = max(range(3), key=lambda index: scores[index])
            selected = [eyes[row][pixel][color] for pixel in range(self.pixels)]
            horizontal = sum(value * math.cos(float(self.angles[pixel])) for pixel, value in enumerate(selected))
            vertical = sum(value * math.sin(float(self.angles[pixel])) for pixel, value in enumerate(selected))
            turns.append(math.atan2(vertical, horizontal) / math.pi)
            bites.append(float(max(selected, default=0.0) > 0.08))
            self.previous_active[row] = active
            self.previous_color[row] = color
            self.previous_bite[row] = bool(bites[-1])
            self.previous_energy[row] = energy[row]
            self.initialized[row] = True

        self.node_count = sum(map(len, self.nodes))
        return torch.tensor(list(zip(turns, [0.72] * self.batch, bites)), dtype=sensors.dtype, device=self.device)

    def structure(self):
        return {"units": self.node_count, "connections": self.node_count}
