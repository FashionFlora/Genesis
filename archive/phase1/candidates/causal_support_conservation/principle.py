"""Causal support is conserved in proportion to local predictive contrast."""

PARAMS = {"timescale": 32.3333333333}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.counts = None
        self.support = 0.0

    def step(self, observation):
        if self.counts is None:
            self.width = len(observation)
            self.counts = [[[[0.0, 0.0] for _ in range(2)]
                            for _ in range(self.width)] for _ in range(self.width)]
        if self.previous is not None:
            decay = PARAMS["timescale"] / (PARAMS["timescale"] + 1.0)
            for source, bit in enumerate(map(int, self.previous)):
                for target, value in enumerate(observation):
                    cell = self.counts[source][target][bit]
                    cell[0] = cell[0] * decay + 1.0
                    cell[1] = cell[1] * decay + value
        prediction = []
        self.support = 0.0
        for target in range(self.width):
            def gap(source):
                pair = self.counts[source][target]
                return abs((pair[1][1] + 1.0) / (pair[1][0] + 2.0)
                           - (pair[0][1] + 1.0) / (pair[0][0] + 2.0))
            source = max(range(self.width), key=gap)
            self.support += gap(source)
            cell = self.counts[source][target][int(observation[source])]
            prediction.append((cell[1] + 1.0) / (cell[0] + 2.0))
        self.previous = list(observation)
        return prediction

    def structure(self):
        return {"units": self.width + self.support,
                "connections": self.support,
                "memory_bytes": self.width * self.width * 32}
