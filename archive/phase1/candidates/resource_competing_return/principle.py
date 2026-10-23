"""Competing relations divide returned sensory resource by predictive fit."""

PARAMS = {"timescale": 16.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.cells = None
        self.prediction = None
        self.edges = 0.0

    def step(self, obs):
        one = True
        two = one + one
        half = one / two
        if self.cells is None:
            self.width = len(obs)
            self.cells = [[[[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
                           for _ in range(self.width)] for _ in range(self.width)]
            self.prediction = [half] * self.width

        if self.previous is not None:
            scale = PARAMS["timescale"]
            for target, after in enumerate(obs):
                fits = []
                for source, before in enumerate(self.previous):
                    state = int(before)
                    cell = self.cells[source][target][state]
                    forecast = (cell[1] + one) / (cell[0] + two)
                    fits.append(one / (one + (forecast - after) ** two))
                total = sum(fits)
                for source, before in enumerate(self.previous):
                    state = int(before)
                    cell = self.cells[source][target][state]
                    share = fits[source] / total
                    cell[0] = (scale * cell[0] + share) / (scale + one)
                    cell[1] = (scale * cell[1] + share * after) / (scale + one)
                    cell[2] = (scale * cell[2] + share) / (scale + one)

        prediction = [half] * self.width
        self.edges = 0.0
        for target in range(self.width):
            def support(source):
                cells = self.cells[source][target]
                contrast = abs((cells[1][1] + one) / (cells[1][0] + two)
                               - (cells[0][1] + one) / (cells[0][0] + two))
                return contrast * (cells[0][2] + cells[1][2] + one)

            source = max(range(self.width), key=support)
            cell = self.cells[source][target][int(obs[source])]
            prediction[target] = (cell[1] + one) / (cell[0] + two)
            self.edges += (target >= self.width // two) * max(
                support(index) for index in range(self.width // two))

        self.previous = list(obs)
        self.prediction = prediction
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * 2 * 24}
