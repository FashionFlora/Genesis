"""A memory address is a locally observable signature of consequences.

Histories share a model when the currently strongest causal edges imply the
same next-state pattern.  A context is retained only through that predictive
signature; global evidence supplies a safe estimate before local evidence is
strong enough.
"""

PARAMS = {"timescale": 8.0, "contexts": 8}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.global_cells = None
        self.local_cells = None
        self.edges = 0.0

    @staticmethod
    def _prob(cell):
        return (cell[1] + 1.0) / (cell[0] + 2.0)

    def _context(self):
        signature = 0
        for target in range(self.width):
            source = max(range(self.width), key=lambda index: self._contrast(index, target))
            pair = self.global_cells[source * self.width + target]
            state = int(self.previous[source])
            signature = (signature * 2 +
                         int(self._prob(pair[state]) >= 0.5)) % int(PARAMS["contexts"])
        return signature

    def _contrast(self, source, target):
        pair = self.global_cells[source * self.width + target]
        return abs(self._prob(pair[1]) - self._prob(pair[0]))

    def step(self, observation):
        if self.global_cells is None:
            self.width = len(observation)
            shape = self.width * self.width
            self.global_cells = [[[0.0, 0.0] for _ in range(2)] for _ in range(shape)]
            self.local_cells = [[[[0.0, 0.0] for _ in range(2)]
                                 for _ in range(int(PARAMS["contexts"]))]
                                for _ in range(shape)]
        context = 0 if self.previous is None else self._context()
        if self.previous is not None:
            decay = PARAMS["timescale"] / (PARAMS["timescale"] + 1.0)
            for source, state in enumerate(self.previous):
                for target, value in enumerate(observation):
                    index = source * self.width + target
                    for cell in (self.global_cells[index][int(state)],
                                 self.local_cells[index][context][int(state)]):
                        cell[0] = decay * cell[0] + 1.0
                        cell[1] = decay * cell[1] + float(value)
        prediction = [0.5] * self.width
        self.edges = 0.0
        if self.previous is not None:
            for target in range(self.width):
                source = max(range(self.width), key=lambda index: self._contrast(index, target))
                index = source * self.width + target
                state = int(self.previous[source])
                global_pair = self.global_cells[index]
                local_cell = self.local_cells[index][context][state]
                global_cell = global_pair[state]
                local_mass = local_cell[0]
                global_mass = sum(cell[0] for cell in global_pair)
                weight = local_mass / (local_mass + global_mass + 1.0)
                prediction[target] = ((1.0 - weight) * self._prob(global_cell) +
                                      weight * self._prob(local_cell))
                self.edges += (target >= self.width / 2 and source < self.width / 2)
        self.previous = list(observation)
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * int(PARAMS["contexts"]) * 32}
