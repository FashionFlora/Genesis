"""Deliberately brittle clock-and-threshold strategy for the judge self-test."""


class System:
    def __init__(self):
        self.clock = 0
        self.regime = 0
        self.active = 1
        self.units = 1
        self.connections = 1

    def step(self, obs):
        self.clock += 1
        slot = self.clock // 208
        if slot == 0:
            self.regime = 0
            self.active = 1
        elif slot == 1:
            self.regime = 1
            self.active = 2
        elif slot == 2:
            self.regime = 2
            self.active = 4
        elif slot == 3:
            self.regime = 3
            self.active = 6
        elif slot == 4:
            self.regime = 0
            self.active = 1
        elif slot == 5:
            self.regime = 3
            self.active = 6
        elif slot == 6:
            self.regime = 2
            self.active = 4
        elif slot == 7:
            self.regime = 1
            self.active = 2
        else:
            self.regime = 0
            self.active = 1

        self.units = self.active
        self.connections = self.active

        sources = [0, 1, 2, 3, 4, 5]
        if self.regime == 1:
            sources = [1, 3, 5, 0, 2, 4]
        elif self.regime == 2:
            sources = [2, 5, 1, 4, 0, 3]
        elif self.regime == 3:
            sources = [3, 2, 0, 5, 1, 4]

        prediction = [0.5 for _ in obs]
        for offset in range(min(6, len(obs) - 6)):
            target = 6 + offset
            if offset < self.active:
                prediction[target] = 0.9 if obs[sources[offset]] else 0.1
            else:
                prediction[target] = 0.8 if obs[target] else 0.2
        return prediction

    def structure(self):
        return {"units": self.units, "connections": self.connections,
                "memory_bytes": self.units * 128 + self.connections * 64}
