"""Contextual recall by reversible selection of the shortest local code."""

PARAMS = {"contexts": 8, "models": 2, "decay": 0.98}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.counts = None
        self.loss = None
        self.edges = 0.0

    def _prob(self, cell):
        return (cell[1] + 1.0) / (cell[0] + 2.0)

    def step(self, obs):
        if self.counts is None:
            self.width = len(obs)
            contexts = int(PARAMS["contexts"])
            models = int(PARAMS["models"])
            self.counts = [[[[[0.0, 0.0] for _ in range(2)]
                             for _ in range(models)]
                            for _ in range(contexts)]
                           for _ in range(self.width * self.width)]
            self.loss = [[[0.0 for _ in range(models)]
                          for _ in range(contexts)]
                         for _ in range(self.width * self.width)]
        context = 0
        if self.previous is not None:
            context = int(sum(self.previous[self.width // 2:])) % int(PARAMS["contexts"])

        prediction = [0.5] * self.width
        self.edges = 0.0
        if self.previous is not None:
            import math
            decay = PARAMS["decay"]
            sources = []
            models = []
            states = []
            for target in range(self.width):
                def contrast(source):
                    index = source * self.width + target
                    bank = self.counts[index][context]
                    model = min(range(len(bank)), key=lambda item: self.loss[index][context][item])
                    return abs(self._prob(bank[model][1]) - self._prob(bank[model][0]))

                source = max(range(self.width), key=contrast)
                index = source * self.width + target
                model = min(range(len(self.counts[index][context])),
                            key=lambda item: self.loss[index][context][item])
                state = int(self.previous[source])
                prediction[target] = self._prob(self.counts[index][context][model][state])
                sources.append(source)
                models.append(model)
                states.append(state)
                if target >= self.width // 2 and source < self.width // 2:
                    self.edges += contrast(source)

            for source, before in enumerate(self.previous):
                state = int(before)
                for target, value in enumerate(obs):
                    index = source * self.width + target
                    bank = self.counts[index][context]
                    choice = min(range(len(bank)), key=lambda item: self.loss[index][context][item])
                    for model in range(len(bank)):
                        probability = self._prob(bank[model][state])
                        cost = -(value * math.log(max(1e-12, probability))
                                 + (1.0 - value) * math.log(max(1e-12, 1.0 - probability)))
                        self.loss[index][context][model] = decay * self.loss[index][context][model] + cost
                    cell = bank[choice][state]
                    cell[0] = decay * cell[0] + 1.0
                    cell[1] = decay * cell[1] + float(value)
        self.previous = list(obs)
        return prediction

    def structure(self):
        return {"units": self.width,
                "connections": self.edges,
                "memory_bytes": self.width * self.width * int(PARAMS["contexts"])
                * int(PARAMS["models"]) * 32}
