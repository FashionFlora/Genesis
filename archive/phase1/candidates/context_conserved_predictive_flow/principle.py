"""Context-local relations retain only the predictive flow they explain."""
PARAMS = {"contexts": 8, "timescale": 16.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.support = None
        self.flow = None
        self.edges = 0.0

    def _address(self, obs):
        contexts = int(PARAMS["contexts"])
        return sum((index + 1) * int(value) for index, value in enumerate(obs)) % contexts

    def step(self, obs):
        if self.support is None:
            self.width = len(obs)
            contexts = int(PARAMS["contexts"])
            self.support = [[[0.0] * self.width for _ in range(self.width)]
                            for _ in range(contexts)]
            self.flow = [[0.0] * self.width for _ in range(contexts)]
            self.previous = list(obs)
            return [0.5] * self.width

        context = self._address(self.previous)
        support = self.support[context]
        flow = self.flow[context]
        scale = float(PARAMS["timescale"])
        prediction = [0.5] * self.width
        for target in range(self.width):
            source = max(range(self.width), key=lambda index: abs(support[index][target]))
            prediction[target] += 0.5 * support[source][target] * (2 * self.previous[source] - 1)
            error = (prediction[target] - obs[target]) ** 2
            flow[target] = (scale * flow[target] + 1.0 / (1.0 + error)) / (scale + 1.0)

        for source, before in enumerate(self.previous):
            x = 2 * before - 1
            for target, after in enumerate(obs):
                y = 2 * after - 1
                rate = flow[target] / (scale + 1.0)
                support[source][target] = (1.0 - rate) * support[source][target] + rate * x * y

        self.edges = sum(max(abs(support[source][target]) for source in range(self.width // 2))
                         for target in range(self.width // 2, self.width))
        self.previous = list(obs)
        return [min(1.0, max(0.0, value)) for value in prediction]

    def structure(self):
        contexts = int(PARAMS["contexts"])
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": contexts * self.width * self.width * 8}
