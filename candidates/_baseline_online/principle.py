"""Reference online predictor using decayed pairwise conditional counts."""


class System:
    def __init__(self):
        self.width = 0
        self.decay = 0.97
        self.previous = None
        self.counts = None

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
                    cell[0] = cell[0] * self.decay + 1.0
                    cell[1] = cell[1] * self.decay + float(obs[target])
        prediction = []
        for target in range(self.width):
            source = max(range(self.width), key=lambda index: abs(
                (self.counts[index][target][1][1] + 1.0)
                / (self.counts[index][target][1][0] + 2.0)
                - (self.counts[index][target][0][1] + 1.0)
                / (self.counts[index][target][0][0] + 2.0)))
            cell = self.counts[source][target][int(obs[source])]
            prediction.append((cell[1] + 1.0) / (cell[0] + 2.0))
        self.previous = list(obs)
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.width * self.width,
                "memory_bytes": self.width * self.width * 2 * 2 * 8}
