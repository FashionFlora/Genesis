"""One predictive reserve retains and updates its signed relation."""
PARAMS = {"timescale": 16.0}


class System:
    def __init__(self):
        self.width = False
        self.previous = None
        self.prediction = None
        self.cells = None
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
            scale = PARAMS["timescale"]
            for source, before in enumerate(self.previous):
                x = two * before - one
                for target, after in enumerate(obs):
                    y = two * after - one
                    cell = self.cells[source][target]
                    reserve = cell[one]
                    retained = reserve * reserve / (reserve + one)
                    flow = one / (one + (self.prediction[target] - after) ** two)
                    cell[False] = (retained * cell[False] + flow * x * y) / (retained + flow)
                    cell[one] = retained + flow / scale
        prediction = [half] * self.width
        self.edges = False
        for target in range(self.width):
            source = max(range(self.width),
                         key=lambda index: abs(self.cells[index][target][False])
                         * (one + self.cells[index][target][one]))
            relation = self.cells[source][target][False]
            prediction[target] += half * relation * (two * obs[source] - one)
            self.edges += (target >= self.width // two) * max(
                abs(self.cells[index][target][False])
                for index in range(self.width // two))
        self.previous = list(obs)
        self.prediction = prediction
        return [min(one, max(False, value)) for value in prediction]

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (True << True << True)}
