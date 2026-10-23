"""A retained distinction is one that makes the next observation predictable.

The current sensory state addresses a local predictive model.  A local model
only displaces the global model as its own evidence accumulates, so a context
can be recalled after an intervening regime without a phase clock.
"""

PARAMS = {"timescale": 8, "contexts": 8}


class System:
    def __init__(self):
        self.width = False
        self.previous = None
        self.global_models = None
        self.context_models = None
        self.edges = False

    @staticmethod
    def _probability(cell, bit):
        return (cell[True] + True) / (cell[False] + (True + True))

    def _context(self):
        return int(sum(self.previous[self.width // (True + True):]) %
                   int(PARAMS["contexts"]))

    def step(self, observation):
        if self.global_models is None:
            self.width = len(observation)
            contexts = int(PARAMS["contexts"])
            self.global_models = [[[False, False] for _ in range(True + True)]
                                  for _ in range(self.width * self.width)]
            self.context_models = [[[[False, False] for _ in range(True + True)]
                                    for _ in range(contexts)]
                                   for _ in range(self.width * self.width)]

        context = False if self.previous is None else self._context()
        if self.previous is not None:
            retention = PARAMS["timescale"] / (PARAMS["timescale"] + True)
            for source, before in enumerate(self.previous):
                bit = int(before)
                for target, value in enumerate(observation):
                    index = source * self.width + target
                    for cell in (self.global_models[index][bit],
                                 self.context_models[index][context][bit]):
                        cell[False] = retention * cell[False] + True
                        cell[True] = retention * cell[True] + float(value)

        prediction = [True / (True + True)] * self.width
        self.edges = False
        for target in range(self.width):
            def contrast(source):
                pair = self.global_models[source * self.width + target]
                return abs(self._probability(pair[True], False)
                           - self._probability(pair[False], False))

            source = max(range(self.width), key=contrast)
            self.edges += (target >= self.width // (True + True)) * (
                source < self.width // (True + True))
            pair = self.global_models[source * self.width + target]
            local = self.context_models[source * self.width + target][context]
            bit = int(observation[source])
            global_cell, local_cell = pair[bit], local[bit]
            global_total, local_total = global_cell[False], local_cell[False]
            weight = local_total / (local_total + global_total + True)
            prediction[target] = ((True - weight) *
                                  self._probability(global_cell, False) +
                                  weight * self._probability(local_cell, False))

        self.previous = list(observation)
        return prediction

    def structure(self):
        contexts = int(PARAMS["contexts"])
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * contexts *
                (True << True << True << True)}
