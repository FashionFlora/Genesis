"""A returning sensory context retrieves the joint model that predicts it."""

PARAMS = {"contexts": 8, "timescale": 8.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.models = None
        self.active = None
        self.edges = 0

    def _blank(self):
        return [[[[0.0, 0.0] for _ in range(2)] for _ in range(self.width)]
                for _ in range(self.width)]

    @staticmethod
    def _prob(cell):
        return (cell[1] + 1.0) / (cell[0] + 2.0)

    def _address(self, obs):
        return sum((index + 1) * int(bit) for index, bit in enumerate(obs)) % int(PARAMS["contexts"])

    def _predict(self, model):
        result = [0.5] * self.width
        for target in range(self.width):
            source = max(range(self.width), key=lambda i: abs(
                self._prob(model[i][target][1]) - self._prob(model[i][target][0])))
            result[target] = self._prob(model[source][target][int(self.previous[source])])
        return result

    def step(self, obs):
        if self.models is None:
            self.width = len(obs)
            contexts = int(PARAMS["contexts"])
            self.models = [[self._blank(), self._blank()] for _ in range(contexts)]
            self.active = [0] * contexts
            self.previous = list(obs)
            return [0.5] * self.width

        context = self._address(self.previous)
        pair = self.models[context]
        estimates = [self._predict(model) for model in pair]
        errors = [sum((prediction[i] - obs[i]) ** 2
                      for i in range(self.width)) for prediction in estimates]
        if errors[1 - self.active[context]] < errors[self.active[context]]:
            self.active[context] = 1 - self.active[context]
        selected = self.active[context]
        prediction = estimates[selected]
        model = pair[selected]
        decay = PARAMS["timescale"] / (PARAMS["timescale"] + 1.0)
        for source, state in enumerate(self.previous):
            bit = int(state)
            for target, value in enumerate(obs):
                cell = model[source][target][bit]
                cell[0] = decay * cell[0] + 1.0
                cell[1] = decay * cell[1] + float(value)

        self.edges = 0
        for target in range(self.width):
            source = max(range(self.width), key=lambda i: abs(
                self._prob(model[i][target][1]) - self._prob(model[i][target][0])))
            self.edges += target >= self.width // 2 and source < self.width // 2
        self.previous = list(obs)
        return prediction

    def structure(self):
        contexts = int(PARAMS["contexts"])
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": contexts * self.width * self.width * 2 * 32}
