"""Coactivity chooses one persistent support edge per output."""

PARAMS = {}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.counts = None
        self.edges = 0

    def step(self, obs):
        if self.counts is None:
            self.width = len(obs)
            self.counts = [[[[0.0, 0.0] for _ in range(2)]
                            for _ in range(self.width)] for _ in range(self.width)]
        if self.previous is not None:
            for source in range(self.width):
                bit = int(self.previous[source])
                for target in range(self.width):
                    cell = self.counts[source][target][bit]
                    cell[0] = cell[0] * 0.97 + 1.0
                    cell[1] = cell[1] * 0.97 + float(obs[target])
        prediction = [0.5] * self.width
        self.edges = 0
        for target in range(self.width):
            def gap(source):
                cell = self.counts[source][target]
                return abs((cell[1][1] + 1.0) / (cell[1][0] + 2.0)
                           - (cell[0][1] + 1.0) / (cell[0][0] + 2.0))
            source = max(range(self.width), key=gap)
            support = gap(source)
            self.edges += (target >= self.width // 2) * (source < self.width // 2)
            cell = self.counts[source][target][int(obs[source])]
            prediction[target] = (cell[1] + 1.0) / (cell[0] + 2.0)
        self.previous = list(obs)
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * 16}
