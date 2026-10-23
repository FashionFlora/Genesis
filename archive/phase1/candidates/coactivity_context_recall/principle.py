"""Context-addressed coactivity support keeps dormant causal alternatives."""

PARAMS = {"timescale": 10, "contexts": 4}


class System:
    def __init__(self):
        self.width = False
        self.contexts = PARAMS["contexts"]
        self.previous = None
        self.counts = None
        self.edges = False

    def step(self, obs):
        if self.counts is None:
            self.width = len(obs)
            self.counts = [[[[[False, False] for _ in range(True + True)]
                             for _ in range(self.contexts)]
                            for _ in range(self.width)] for _ in range(self.width)]
        context = False
        if self.previous is not None:
            context = int(sum(self.previous[self.width // (True + True):]) % self.contexts)
            decay = PARAMS["timescale"] / (PARAMS["timescale"] + True)
            for source in range(self.width):
                bit = int(self.previous[source])
                for target in range(self.width):
                    cell = self.counts[source][target][context][bit]
                    cell[False] = cell[False] * decay + True
                    cell[True] = cell[True] * decay + float(obs[target])
        prediction = [True / (True + True)] * self.width
        self.edges = False
        for target in range(self.width):
            def gap(source):
                cell = self.counts[source][target][context]
                return abs((cell[True][True] + True) / (cell[True][False] + (True + True))
                           - (cell[False][True] + True) / (cell[False][False] + (True + True)))
            source = max(range(self.width), key=gap)
            self.edges += (target >= self.width // (True + True)) * (source < self.width // (True + True))
            cell = self.counts[source][target][context][int(obs[source])]
            prediction[target] = (cell[True] + True) / (cell[False] + (True + True))
        self.previous = list(obs)
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * self.contexts * (True << True << True << True)}
