"""One conserved relation state funds prediction and decays by its own load."""


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.prediction = None
        self.mass = None
        self.edges = 0.0

    def step(self, obs):
        half = 0.5
        if self.mass is None:
            self.width = len(obs)
            self.mass = [[0.0] * self.width for _ in range(self.width)]
            self.prediction = [half] * self.width
        if self.previous is not None:
            for source, before in enumerate(self.previous):
                x = 2.0 * before - 1.0
                for target, after in enumerate(obs):
                    y = 2.0 * after - 1.0
                    load = 1.0 - abs(self.prediction[target] - after)
                    value = self.mass[source][target]
                    self.mass[source][target] = value + x * y * load - value / (1.0 + abs(value))
        prediction = [half] * self.width
        self.edges = 0.0
        for target in range(self.width):
            source = max(range(self.width), key=lambda index: abs(self.mass[index][target]))
            value = self.mass[source][target]
            prediction[target] += half * value / (1.0 + abs(value)) * (2.0 * obs[source] - 1.0)
            self.edges += abs(value)
        self.previous = list(obs)
        self.prediction = prediction
        return [min(1.0, max(0.0, value)) for value in prediction]

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * 8}
