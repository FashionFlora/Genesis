"""A finite update budget flows toward locally supported coactivity traces."""

PARAMS = {"timescale": 20}


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

        supports = [[0.0] * self.width for _ in range(self.width)]
        if self.previous is not None:
            decay = PARAMS["timescale"] / (PARAMS["timescale"] + 1)
            for source in range(self.width):
                bit = int(self.previous[source])
                for target in range(self.width):
                    cell = self.counts[source][target][bit]
                    cell[0] *= decay
                    cell[1] *= decay
                    supports[source][target] = abs(
                        (cell[1] + 1) / (cell[0] + 2)
                        - (self.counts[source][target][1 - bit][1] + 1)
                        / (self.counts[source][target][1 - bit][0] + 2))

            # Preserve the old total evidence inflow while redistributing it.
            for target in range(self.width):
                total = sum(supports[source][target] + 1
                            for source in range(self.width))
                for source in range(self.width):
                    cell = self.counts[source][target][int(self.previous[source])]
                    share = self.width * (supports[source][target] + 1) / total
                    cell[0] += share
                    cell[1] += share * float(obs[target])

        prediction = [0.5] * self.width
        self.edges = 0
        for target in range(self.width):
            def support(source):
                cell = self.counts[source][target]
                return abs((cell[1][1] + 1) / (cell[1][0] + 2)
                           - (cell[0][1] + 1) / (cell[0][0] + 2))

            source = max(range(self.width), key=support)
            self.edges += (target >= self.width // 2) * (source < self.width // 2)
            cell = self.counts[source][target][int(obs[source])]
            prediction[target] = (cell[1] + 1) / (cell[0] + 2)

        self.previous = list(obs)
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * 16}
