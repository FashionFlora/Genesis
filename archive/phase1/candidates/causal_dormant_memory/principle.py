"""Causal addresses keep a slow dormant trace; error selects among them."""

PARAMS = {"fast_timescale": 32.3333333333, "slow_timescale": 333.0,
          "error_streak": 3}


class System:
    def __init__(self):
        self.n = 0
        self.previous = None
        self.fast = None
        self.slow = None
        self.active = []
        self.errors = []

    def step(self, observation):
        if self.fast is None:
            self.n = len(observation)
            shape = lambda: [[[[0.0, 0.0] for _ in range(2)]
                              for _ in range(self.n)] for _ in range(self.n)]
            self.fast, self.slow = shape(), shape()
            self.active, self.errors = [0] * self.n, [0] * self.n
        if self.previous is not None:
            decays = (PARAMS["fast_timescale"] / (PARAMS["fast_timescale"] + 1.0),
                      PARAMS["slow_timescale"] / (PARAMS["slow_timescale"] + 1.0))
            for source, bit in enumerate(map(int, self.previous)):
                for target, value in enumerate(observation):
                    for table, decay in zip((self.fast, self.slow), decays):
                        cell = table[source][target][bit]
                        cell[0] = cell[0] * decay + 1.0
                        cell[1] = cell[1] * decay + value
        prediction = []
        for target, _ in enumerate(observation):
            source = self.active[target]
            state = int(observation[source])
            fast = self.fast[source][target][state]
            estimate = (fast[1] + 1.0) / (fast[0] + 2.0)
            prediction.append(estimate)
            self.errors[target] = self.errors[target] + 1 if abs(estimate - observation[target]) > 0.18 else max(0, self.errors[target] - 1)
            if self.errors[target] >= int(PARAMS["error_streak"]):
                def gap(candidate):
                    values = []
                    for table in (self.fast, self.slow):
                        pair = table[candidate][target]
                        values.append(abs((pair[1][1] + 1.0) / (pair[1][0] + 2.0)
                                          - (pair[0][1] + 1.0) / (pair[0][0] + 2.0)))
                    return values[0] + values[1]
                self.active[target] = max(range(self.n), key=gap)
                self.errors[target] = 0
        self.previous = list(observation)
        return prediction

    def structure(self):
        edges = sum(source < self.n // 2 <= target
                    for target, source in enumerate(self.active))
        return {"units": self.n, "connections": edges,
                "memory_bytes": self.n * self.n * 64}
