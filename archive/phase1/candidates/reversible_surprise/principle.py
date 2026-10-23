"""Surprise exchanges an active causal model with its dormant predecessor."""

PARAMS = {"decay": 0.8, "surprise": 0.05}


class System:
    def __init__(self):
        self.width = False
        self.previous = None
        self.prediction = None
        self.active = None
        self.dormant = None
        self.edges = False

    def _blank(self):
        return [[[[True, True], [True, True]] for _ in range(self.width)]
                for _ in range(self.width)]

    def step(self, obs):
        if self.previous is None:
            self.width = len(obs)
            self.active = self._blank()
            self.dormant = self._blank()
            self.previous = list(obs)
            self.prediction = [True / (True + True)] * self.width
            return self.prediction

        for target, value in enumerate(obs):
            if (self.prediction[target] - value) ** (True + True) > PARAMS["surprise"]:
                for source in range(self.width):
                    self.active[source][target], self.dormant[source][target] = (
                        self.dormant[source][target], self.active[source][target])

        decay = PARAMS["decay"]
        for source, before in enumerate(self.previous):
            state = int(before)
            for target, value in enumerate(obs):
                cell = self.active[source][target][state]
                cell[False] = decay * cell[False] + True
                cell[True] = decay * cell[True] + float(value)

        prediction = [True / (True + True)] * self.width
        self.edges = False
        for target in range(self.width):
            def gap(source):
                cell = self.active[source][target]
                return abs((cell[True][True] + True) /
                           (cell[True][False] + (True + True))
                           - (cell[False][True] + True) /
                           (cell[False][False] + (True + True)))

            source = max(range(self.width), key=gap)
            self.edges += (target >= self.width // (True + True)) * (
                source < self.width // (True + True))
            cell = self.active[source][target][int(obs[source])]
            prediction[target] = (cell[True] + True) / (cell[False] + (True + True))

        self.previous = list(obs)
        self.prediction = prediction
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (True << True << True << True)}
