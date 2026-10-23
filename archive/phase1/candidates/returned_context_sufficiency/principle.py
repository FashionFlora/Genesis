"""A context-addressed relation persists through confirmed consequences."""

PARAMS = {"timescale": 8.0, "contexts": 8}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.models = None
        self.edges = 0.0

    @staticmethod
    def _probability(cell):
        return (cell[1] + 1.0) / (cell[0] + 2.0)

    def step(self, observation):
        if self.models is None:
            self.width = len(observation)
            contexts = int(PARAMS["contexts"])
            self.models = [[[[0.0, 0.0] for _ in range(2)]
                            for _ in range(contexts)]
                           for _ in range(self.width * self.width)]

        context = 0
        if self.previous is not None:
            context = int(sum(self.previous[1:])) % int(PARAMS["contexts"])

        predictions = [0.5] * self.width
        chosen = []
        self.edges = 0.0
        if self.previous is not None:
            for target in range(self.width):
                def score(source):
                    index = source * self.width + target
                    pair = self.models[index][context]
                    contrast = abs(self._probability(pair[1]) - self._probability(pair[0]))
                    evidence = min(1.0, sum(cell[0] for cell in pair) / 4.0)
                    return contrast * evidence

                source = max(range(self.width), key=score)
                cell = self.models[source * self.width + target][context][int(self.previous[source])]
                predictions[target] = self._probability(cell)
                chosen.append(source)
                if target >= self.width // 2 and source < self.width // 2:
                    self.edges += score(source)

            retention = PARAMS["timescale"] / (PARAMS["timescale"] + 1.0)
            for source, before in enumerate(self.previous):
                bit = int(before)
                for target, value in enumerate(observation):
                    cell = self.models[source * self.width + target][context][bit]
                    prior = self._probability(cell)
                    returned = 1.0 - abs(prior - float(value))
                    cell[0] = retention * cell[0] + returned
                    cell[1] = retention * cell[1] + returned * float(value)

        self.previous = list(observation)
        return predictions

    def structure(self):
        return {"units": self.width,
                "connections": self.edges,
                "memory_bytes": self.width * self.width * int(PARAMS["contexts"]) * 32}
