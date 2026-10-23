"""A contact persists only as long as its retained coactivity can pay its next update."""


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.reserve = None
        self.mass = 0.0

    def step(self, obs):
        if self.reserve is None:
            self.width = len(obs)
            self.reserve = [[0.0] * self.width for _ in range(self.width)]
        if self.previous is not None:
            for source, before in enumerate(self.previous):
                x = 2.0 * before - 1.0
                for target, after in enumerate(obs):
                    y = 2.0 * after - 1.0
                    old = self.reserve[source][target]
                    retained = old * abs(old) / (abs(old) + 1.0)
                    incoming = retained + x * y
                    self.reserve[source][target] = incoming / (1.0 + abs(incoming))
        prediction = [0.5] * self.width
        self.mass = 0.0
        for target in range(self.width):
            source = max(range(self.width), key=lambda index: abs(self.reserve[index][target]))
            support = self.reserve[source][target]
            self.mass += abs(support) * (target >= self.width / 2.0) * (source < self.width / 2.0)
            prediction[target] += 0.5 * support * (2.0 * obs[source] - 1.0)
        self.previous = list(obs)
        return [min(1.0, max(0.0, value)) for value in prediction]

    def structure(self):
        return {"units": self.width, "connections": self.mass,
                "memory_bytes": self.width * self.width * 8}
