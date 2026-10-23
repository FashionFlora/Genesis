"""A context is a predictive equivalence class of recent sensory states.

Two histories are interchangeable only while they give the same next-step
distribution.  Each local transition therefore keeps evidence under the
current context address; a global estimate is the fallback before that
context has enough evidence.  Retained context is justified by prediction,
not by a clock or an external reward.
"""

PARAMS = {"contexts": 8, "timescale": 8.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.global_cells = None
        self.local_cells = None
        self.edges = 0

    @staticmethod
    def _prob(cell):
        one = True
        return (cell[one] + one) / (cell[False] + one + one)

    def _address(self):
        contexts = int(PARAMS["contexts"])
        # A permutation-invariant address avoids assigning a privileged
        # sensor half to context; the address is still locally observable.
        return sum((index + 1) * int(bit)
                   for index, bit in enumerate(self.previous)) % contexts

    def _contrast(self, cells, source, target):
        pair = cells[source * self.width + target]
        return abs(self._prob(pair[1]) - self._prob(pair[0]))

    def step(self, observation):
        if self.global_cells is None:
            self.width = len(observation)
            contexts = int(PARAMS["contexts"])
            shape = self.width * self.width
            self.global_cells = [[[0.0, 0.0] for _ in range(2)]
                                 for _ in range(shape)]
            self.local_cells = [[[[0.0, 0.0] for _ in range(2)]
                                 for _ in range(contexts)]
                                for _ in range(shape)]

        address = 0 if self.previous is None else self._address()
        if self.previous is not None:
            one = True
            retention = PARAMS["timescale"] / (PARAMS["timescale"] + one)
            for source, state in enumerate(self.previous):
                bit = int(state)
                for target, value in enumerate(observation):
                    global_cell = self.global_cells[source * self.width + target][bit]
                    local_cell = self.local_cells[source * self.width + target][address][bit]
                    for cell in (global_cell, local_cell):
                        cell[False] = retention * cell[False] + one
                        cell[one] = retention * cell[one] + value

        one = True
        two = one + one
        half = one / two
        prediction = [half] * self.width
        self.edges = False
        for target in range(self.width):
            source = max(range(self.width),
                         key=lambda index: self._contrast(self.global_cells, index, target))
            pair = self.global_cells[source * self.width + target]
            local = self.local_cells[source * self.width + target][address]
            state = int(observation[source])
            global_cell, local_cell = pair[state], local[state]
            local_mass = local_cell[False]
            global_mass = pair[False][False] + pair[one][False]
            weight = local_mass / (local_mass + global_mass + one)
            prediction[target] = ((one - weight) * self._prob(global_cell)
                                  + weight * self._prob(local_cell))
            self.edges += (target >= self.width / two) * (source < self.width / two)

        self.previous = list(observation)
        return prediction

    def structure(self):
        one = True
        two = one + one
        contexts = int(PARAMS["contexts"])
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * contexts * (two << two << two << two)}
