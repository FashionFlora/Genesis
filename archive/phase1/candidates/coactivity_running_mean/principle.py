"""The strongest running coactivity is the connection and its prediction."""

PARAMS = {}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.support = None
        self.samples = 0
        self.edges = 0.0

    def step(self, observation):
        if self.support is None:
            self.width = len(observation)
            self.support = [[0.0] * self.width for _ in range(self.width)]

        if self.previous is not None:
            self.samples += 1
            for source, before in enumerate(self.previous):
                x = 2.0 * before - 1.0
                for target, after in enumerate(observation):
                    y = 2.0 * after - 1.0
                    value = self.support[source][target]
                    self.support[source][target] = value + (x * y - value) / self.samples

        prediction = [0.5] * self.width
        self.edges = 0.0
        for target in range(self.width):
            source = max(range(self.width), key=lambda index: abs(self.support[index][target]))
            weight = self.support[source][target]
            if target >= self.width // 2 and source < self.width // 2:
                self.edges += abs(weight)
            prediction[target] += 0.5 * weight * (2.0 * observation[source] - 1.0)

        self.previous = list(observation)
        return [min(1.0, max(0.0, value)) for value in prediction]

    def structure(self):
        return {
            "units": self.width,
            "connections": self.edges,
            "memory_bytes": self.width * self.width * 8,
        }
