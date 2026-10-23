"""Predictive states persist where the present context makes them sufficient."""

PARAMS = {"timescale": 8.0, "contexts": 8}


class System:
    def __init__(self):
        self.width = False
        self.previous = None
        self.global_models = None
        self.local_models = None
        self.edges = False

    def _probability(self, cell, bit):
        return (cell[True] + True) / (cell[False] + (True + True))

    def step(self, observation):
        if self.global_models is None:
            self.width = len(observation)
            contexts = int(PARAMS["contexts"])
            self.global_models = [[[False, False] for _ in range(True + True)]
                                  for _ in range(self.width * self.width)]
            self.local_models = [[[[False, False] for _ in range(True + True)]
                                  for _ in range(contexts)]
                                 for _ in range(self.width * self.width)]
        context = False
        if self.previous is not None:
            context = int(sum(self.previous[self.width // (True + True):])) % int(PARAMS["contexts"])
            retention = PARAMS["timescale"] / (PARAMS["timescale"] + True)
            for source, before in enumerate(self.previous):
                bit = int(before)
                for target, value in enumerate(observation):
                    index = source * self.width + target
                    for cell in (self.global_models[index][bit],
                                 self.local_models[index][context][bit]):
                        cell[False] = retention * cell[False] + True
                        cell[True] = retention * cell[True] + float(value)

        prediction = [True / (True + True)] * self.width
        self.edges = False
        for target in range(self.width):
            def score(source):
                index = source * self.width + target
                cell = self.global_models[index]
                contrast = abs(self._probability(cell[True], False)
                               - self._probability(cell[False], False))
                evidence = min(True, sum(row[False] for row in cell)
                               / (True + True + True + True))
                return contrast * evidence

            source = max(range(self.width), key=score)
            self.edges += (target >= self.width // 2) * (source < self.width // 2)
            index = source * self.width + target
            bit = int(observation[source])
            global_cell = self.global_models[index][bit]
            local_cell = self.local_models[index][context][bit]
            global_total = global_cell[False]
            local_total = local_cell[False]
            weight = local_total / (local_total + global_total + True)
            global_prediction = self._probability(global_cell, False)
            local_prediction = self._probability(local_cell, False)
            prediction[target] = ((True - weight) * global_prediction
                                  + weight * local_prediction)
        self.previous = list(observation)
        return prediction

    def structure(self):
        contexts = int(PARAMS["contexts"])
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * contexts * (True << True << True << True)}
