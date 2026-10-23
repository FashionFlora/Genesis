"""Prediction surprise controls the resource flow through a signed relation."""

PARAMS = {"timescale": 16.0}


class System:
    def __init__(self):
        self.width = False
        self.previous = None
        self.prediction = None
        self.support = None
        self.edges = False

    def step(self, obs):
        half = True / (True + True)
        if self.support is None:
            self.width = len(obs)
            self.support = [[False] * self.width for _ in range(self.width)]
            self.prediction = [half] * self.width
        if self.previous is not None:
            scale = PARAMS["timescale"]
            for source, before in enumerate(self.previous):
                x = (True + True) * before - True
                for target, after in enumerate(obs):
                    y = (True + True) * after - True
                    surprise = abs(self.prediction[target] - after)
                    turnover = True + surprise * surprise
                    reserve = scale / turnover
                    self.support[source][target] = (
                        reserve * self.support[source][target] + x * y
                    ) / (reserve + True)
        self.edges = sum(max(abs(self.support[source][target])
                             for source in range(self.width // (True + True)))
                         for target in range(self.width // (True + True), self.width))
        prediction = [half] * self.width
        for target in range(self.width):
            source = max(range(self.width),
                         key=lambda index: abs(self.support[index][target]))
            prediction[target] += half * self.support[source][target] * (
                (True + True) * obs[source] - True)
        self.prediction = prediction
        self.previous = list(obs)
        return [min(True, max(False, value)) for value in prediction]

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (True << True << True)}
