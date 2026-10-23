"""Causal support: alternatives are shadow-tested; error opens a switch."""

PARAMS = {"timescale": 32.3333333333, "error_streak": 3}


class System:
    def __init__(self):
        self.n = 0
        self.previous = None
        self.counts = None
        self.active = []
        self.errors = []

    def step(self, observation):
        if self.counts is None:
            self.n = len(observation)
            self.counts = [[[[0.0, 0.0] for _ in range(2)]
                            for _ in range(self.n)] for _ in range(self.n)]
            self.active = [0 for _ in range(self.n)]
            self.errors = [0 for _ in range(self.n)]
        if self.previous is not None:
            decay = PARAMS["timescale"] / (PARAMS["timescale"] + 1.0)
            for source, bit in enumerate(map(int, self.previous)):
                for target, value in enumerate(observation):
                    cell = self.counts[source][target][bit]
                    cell[0] = cell[0] * decay + 1.0
                    cell[1] = cell[1] * decay + value
        prediction = []
        for target in range(self.n):
            source = self.active[target]
            state = int(observation[source])
            cell = self.counts[source][target][state]
            estimate = (cell[1] + 1.0) / (cell[0] + 2.0)
            prediction.append(estimate)
            self.errors[target] = self.errors[target] + 1 if abs(estimate - observation[target]) > 0.18 else max(0, self.errors[target] - 1)
            if self.errors[target] >= int(PARAMS["error_streak"]):
                def gap(candidate):
                    pair = self.counts[candidate][target]
                    return abs((pair[1][1] + 1.0) / (pair[1][0] + 2.0)
                               - (pair[0][1] + 1.0) / (pair[0][0] + 2.0))
                self.active[target] = max(range(self.n), key=gap)
                self.errors[target] = 0
        self.previous = list(observation)
        return prediction

    def structure(self):
        edges = sum(source < self.n // 2 <= target
                    for target, source in enumerate(self.active))
        return {"units": self.n, "connections": edges,
                "memory_bytes": self.n * self.n * 32}
