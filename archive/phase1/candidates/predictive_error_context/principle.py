"""Context persists as the recurrent pattern of unresolved prediction error."""

PARAMS = {"timescale": 8.0, "contexts": 8}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.prediction = None
        self.context = 0
        self.global_cells = None
        self.local_cells = None
        self.edges = 0

    @staticmethod
    def _prob(cell):
        return (cell[1] + 1.0) / (cell[0] + 2.0)

    def _address(self, errors):
        return int(sum((index + 1) * int(error) for index, error in enumerate(errors))
                   % max(1, int(PARAMS["contexts"])))

    def step(self, observation):
        if self.global_cells is None:
            self.width = len(observation)
            shape = self.width * self.width
            contexts = max(1, int(PARAMS["contexts"]))
            self.global_cells = [[[0.0, 0.0] for _ in range(2)] for _ in range(shape)]
            self.local_cells = [[[[0.0, 0.0] for _ in range(2)]
                                 for _ in range(contexts)] for _ in range(shape)]
            self.previous = list(observation)
            self.prediction = [0.5] * self.width
            return list(self.prediction)

        if self.previous is not None:
            retention = PARAMS["timescale"] / (PARAMS["timescale"] + 1.0)
            for source, before in enumerate(self.previous):
                state = int(before)
                for target, value in enumerate(observation):
                    index = source * self.width + target
                    for cell in (self.global_cells[index][state],
                                 self.local_cells[index][self.context][state]):
                        cell[0] = retention * cell[0] + 1.0
                        cell[1] = retention * cell[1] + float(value)

        prediction = [0.5] * self.width
        self.edges = 0.0
        for target in range(self.width):
            source = max(range(self.width), key=lambda item: abs(
                self._prob(self.global_cells[item * self.width + target][1]) -
                self._prob(self.global_cells[item * self.width + target][0])))
            index = source * self.width + target
            state = int(observation[source])
            global_cell = self.global_cells[index][state]
            local_cell = self.local_cells[index][self.context][state]
            mass = local_cell[0]
            total = sum(cell[0] for cell in self.global_cells[index])
            weight = mass / (mass + total + 1.0)
            prediction[target] = ((1.0 - weight) * self._prob(global_cell)
                                  + weight * self._prob(local_cell))
            self.edges += (target >= self.width / 2.0) * (source < self.width / 2.0)

        errors = [int((guess >= 0.5) != bool(value))
                  for guess, value in zip(self.prediction, observation)]
        self.context = self._address(errors)
        self.previous, self.prediction = list(observation), prediction
        return list(prediction)

    def structure(self):
        contexts = max(1, int(PARAMS["contexts"]))
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * contexts * 16}
