"""One bounded coactivity state is the edge, forecast, and structure."""

PARAMS = {"timescale": 16.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.support = None
        self.edges = 0

    def step(self, observation):
        if self.support is None:
            self.width = len(observation)
            self.support = [[0.0] * self.width for _ in range(self.width)]
        if self.previous is not None:
            scale = PARAMS["timescale"]
            for source, before in enumerate(self.previous):
                x = 2.0 * before - 1.0
                for target, after in enumerate(observation):
                    y = 2.0 * after - 1.0
                    self.support[source][target] = (
                        scale * self.support[source][target] + x * y
                    ) / (scale + 1.0)
        prediction = [0.5] * self.width
        self.edges = 0
        for target in range(self.width):
            source = max(range(self.width),
                         key=lambda index: abs(self.support[index][target]))
            strength = self.support[source][target]
            self.edges += int(target >= self.width / 2.0 and source < self.width / 2.0)
            prediction[target] += 0.5 * strength * (2.0 * observation[source] - 1.0)
        self.previous = list(observation)
        return [min(1.0, max(0.0, value)) for value in prediction]

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * 8}
