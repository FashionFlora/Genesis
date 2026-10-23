"""A dormant local predictor can replace its active predecessor only if it wins."""

PARAMS = {"decay": 0.8, "margin": 0.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.prediction = None
        self.active = None
        self.dormant = None
        self.edges = 0

    def _blank(self):
        return [[[[1.0, 1.0], [1.0, 1.0]] for _ in range(self.width)]
                for _ in range(self.width)]

    @staticmethod
    def _prob(cell, state):
        return (cell[state][1] + 1.0) / (cell[state][0] + 2.0)

    def _source(self, model, target):
        return max(
            range(self.width),
            key=lambda index: abs(
                self._prob(model[index][target], 1)
                - self._prob(model[index][target], 0)))

    def step(self, obs):
        if self.previous is None:
            self.width = len(obs)
            self.active = self._blank()
            self.dormant = self._blank()
            self.previous = list(obs)
            self.prediction = [0.5] * self.width
            return self.prediction

        for target, value in enumerate(obs):
            active_source = self._source(self.active, target)
            dormant_source = self._source(self.dormant, target)
            active_error = (self._prob(
                self.active[active_source][target], int(self.previous[active_source])) - value) ** 2
            dormant_error = (self._prob(
                self.dormant[dormant_source][target], int(self.previous[dormant_source])) - value) ** 2
            if dormant_error + PARAMS["margin"] < active_error:
                for source in range(self.width):
                    self.active[source][target], self.dormant[source][target] = (
                        self.dormant[source][target], self.active[source][target])

        decay = PARAMS["decay"]
        for source, before in enumerate(self.previous):
            state = int(before)
            for target, value in enumerate(obs):
                cell = self.active[source][target][state]
                cell[0] = decay * cell[0] + 1.0
                cell[1] = decay * cell[1] + float(value)

        prediction = [0.5] * self.width
        self.edges = 0
        for target in range(self.width):
            source = max(
                range(self.width),
                key=lambda index: abs(
                    self._prob(self.active[index][target], 1)
                    - self._prob(self.active[index][target], 0)))
            self.edges += target >= self.width // 2 and source < self.width // 2
            prediction[target] = self._prob(
                self.active[source][target], int(obs[source]))

        self.previous = list(obs)
        self.prediction = prediction
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * 16}
