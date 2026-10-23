"""Context addresses local model pairs; prediction error retrieves a model."""

PARAMS = {"contexts": 4, "decay": 0.8}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.models = None
        self.errors = None
        self.edges = 0

    def _blank(self):
        return [[[[1.0, 1.0], [1.0, 1.0]] for _ in range(self.width)]
                for _ in range(self.width)]

    @staticmethod
    def _prob(cell, state):
        return (cell[state][1] + 1.0) / (cell[state][0] + 2.0)

    def _address(self, obs):
        width = min(len(obs), (int(PARAMS["contexts"]) - 1).bit_length())
        return sum(int(obs[index]) << index for index in range(width)) % int(PARAMS["contexts"])

    def step(self, obs):
        if self.models is None:
            self.width = len(obs)
            contexts = int(PARAMS["contexts"])
            self.models = [[self._blank(), self._blank()] for _ in range(contexts)]
            self.errors = [[0.0, 0.0] for _ in range(contexts * self.width)]
            self.previous = list(obs)
            return [0.5] * self.width

        address = self._address(self.previous)
        pair = self.models[address]
        decay = PARAMS["decay"]
        prediction = [0.5] * self.width
        for target, value in enumerate(obs):
            slot = address * self.width + target
            estimates = []
            for model in pair:
                source = max(range(self.width), key=lambda index: abs(
                    self._prob(model[index][target], 1) - self._prob(model[index][target], 0)))
                estimates.append(self._prob(model[source][target], int(self.previous[source])))
            active = min(range(2), key=lambda index: self.errors[slot][index])
            prediction[target] = estimates[active]
            for index, estimate in enumerate(estimates):
                error = (estimate - value) ** 2
                self.errors[slot][index] = decay * self.errors[slot][index] + (1.0 - decay) * error
            model = pair[active]
            for source, before in enumerate(self.previous):
                cell = model[source][target][int(before)]
                cell[0] = decay * cell[0] + 1.0
                cell[1] = decay * cell[1] + float(value)

        self.edges = 0
        for target in range(self.width):
            source = max(range(self.width), key=lambda index: abs(
                self._prob(pair[0][index][target], 1) - self._prob(pair[0][index][target], 0)))
            self.edges += target >= self.width // 2 and source < self.width // 2
        self.previous = list(obs)
        return prediction

    def structure(self):
        contexts = int(PARAMS["contexts"])
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": contexts * self.width * self.width * 32}
