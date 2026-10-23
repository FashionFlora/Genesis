"""One local correlation state is edge, predictor, and structural memory."""

PARAMS = {"decay": 0.97}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.support = None

    def step(self, obs):
        if self.support is None:
            self.width = len(obs)
            self.support = [[0.0 for _ in range(self.width)]
                            for _ in range(self.width)]
        if self.previous is not None:
            for source, before in enumerate(self.previous):
                for target, after in enumerate(obs):
                    coactivity = (2.0 * before - 1.0) * (2.0 * after - 1.0)
                    self.support[source][target] = (
                        PARAMS["decay"] * self.support[source][target]
                        + (1.0 - PARAMS["decay"]) * coactivity)
        prediction = [0.5] * self.width
        for target in range(self.width):
            source = max(range(self.width),
                         key=lambda index: abs(self.support[index][target]))
            prediction[target] += (
                0.5 * self.support[source][target] * (2.0 * obs[source] - 1.0))
        self.previous = list(obs)
        return [min(1.0, max(0.0, value)) for value in prediction]

    def structure(self):
        mass = sum(abs(value) for row in self.support for value in row)
        return {"units": self.width + mass, "connections": mass,
                "memory_bytes": self.width * self.width * 8}
