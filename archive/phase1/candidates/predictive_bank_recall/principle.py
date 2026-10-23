"""Retrieve whichever retained local model best explains recent transitions."""

PARAMS = {"decay": 0.8}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.models = None
        self.losses = None
        self.edges = 0

    @staticmethod
    def _blank(width):
        return [[[[1.0, 1.0], [1.0, 1.0]] for _ in range(width)]
                for _ in range(width)]

    @staticmethod
    def _probability(cell, bit):
        return (cell[bit][1] + 1.0) / (cell[bit][0] + 2.0)

    def step(self, observation):
        if self.models is None:
            self.width = len(observation)
            self.models = [self._blank(self.width), self._blank(self.width)]
            self.losses = [[0.0, 0.0] for _ in range(self.width)]
            self.previous = list(observation)
            return [0.5] * self.width

        decay = PARAMS["decay"]
        prediction = []
        choices = []
        alternatives = []
        for target in range(self.width):
            estimates = []
            for model in self.models:
                source = max(range(self.width), key=lambda index: abs(
                    self._probability(model[index][target], 1)
                    - self._probability(model[index][target], 0)))
                estimates.append(self._probability(
                    model[source][target], int(self.previous[source])))
            chosen = min(range(2), key=lambda bank: self.losses[target][bank])
            prediction.append(estimates[chosen])
            choices.append(chosen)
            alternatives.append(estimates)

        for target, value in enumerate(observation):
            for bank in range(2):
                error = (alternatives[target][bank] - value) ** 2
                self.losses[target][bank] = (
                    decay * self.losses[target][bank] + (1.0 - decay) * error)
            model = self.models[choices[target]]
            for source, before in enumerate(self.previous):
                cell = model[source][target][int(before)]
                cell[0] = decay * cell[0] + 1.0
                cell[1] = decay * cell[1] + float(value)

        self.edges = 0
        for target in range(self.width):
            source = max(range(self.width), key=lambda index: abs(
                self._probability(self.models[0][index][target], 1)
                - self._probability(self.models[0][index][target], 0)))
            self.edges += target >= self.width // 2 and source < self.width // 2
        self.previous = list(observation)
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * 2 * 16}
