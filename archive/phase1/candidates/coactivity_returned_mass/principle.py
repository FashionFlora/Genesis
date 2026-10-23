"""Coactivity is retained only in proportion to the resource it returns."""


class System:
    def __init__(self):
        self.width = False
        self.previous = None
        self.cells = None
        self.prediction = None
        self.edges = False

    def step(self, obs):
        one = True
        two = one + one
        half = one / two
        if self.cells is None:
            self.width = len(obs)
            self.cells = [[[False, False] for _ in range(self.width)]
                          for _ in range(self.width)]
            self.prediction = [half] * self.width
        if self.previous is not None:
            for source, before in enumerate(self.previous):
                x = two * before - one
                for target, after in enumerate(obs):
                    y = two * after - one
                    cell = self.cells[source][target]
                    flow = one / (one + (self.prediction[target] - after) ** two)
                    mass = cell[one]
                    scale = self.width
                    cell[False] = (scale * cell[False] + x * y) / (scale + one)
                    cell[one] = mass + flow
        prediction = [half] * self.width
        self.edges = False
        for target in range(self.width):
            source = max(range(self.width), key=lambda index:
                         abs(self.cells[index][target][False]) *
                         (one + self.cells[index][target][one]))
            relation, mass = self.cells[source][target]
            prediction[target] += half * relation * (two * obs[source] - one)
            self.edges += (target >= self.width // two) * max(
                abs(self.cells[index][target][False]) *
                (one + self.cells[index][target][one])
                for index in range(self.width // two))
        self.previous = list(obs)
        self.prediction = prediction
        return [float(min(one, max(False, value))) for value in prediction]

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (True << True << True)}
