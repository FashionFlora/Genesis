"""A distinction persists when its predicted consequence persists.

Fast evidence follows the current regime; a slow trace keeps a causal
consequence available when the regime returns.  The current observation is
only an address for that consequence, not a stored phase or reward.
"""

PARAMS = {"fast_timescale": 8.0, "slow_timescale": 64.0, "contexts": 8}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.fast = None
        self.slow = None
        self.edges = 0.0

    @staticmethod
    def _prob(cell, state):
        return (cell[state][1] + 1.0) / (cell[state][0] + 2.0)

    def _address(self, observation):
        return int(sum((index + 1) * int(bit)
                       for index, bit in enumerate(observation)) %
                   int(PARAMS["contexts"]))

    def step(self, observation):
        if self.fast is None:
            self.width = len(observation)
            shape = lambda: [[[[0.0, 0.0] for _ in range(2)]
                              for _ in range(int(PARAMS["contexts"]))]
                             for _ in range(self.width * self.width)]
            self.fast, self.slow = shape(), shape()
        context = 0 if self.previous is None else self._address(self.previous)
        prediction = [0.5] * self.width
        self.edges = 0.0
        if self.previous is not None:
            fast_decay = PARAMS["fast_timescale"] / (PARAMS["fast_timescale"] + 1.0)
            slow_decay = PARAMS["slow_timescale"] / (PARAMS["slow_timescale"] + 1.0)
            for source, state in enumerate(self.previous):
                for target, value in enumerate(observation):
                    index = source * self.width + target
                    for table, decay in ((self.fast, fast_decay), (self.slow, slow_decay)):
                        cell = table[index][context][int(state)]
                        cell[0] = decay * cell[0] + 1.0
                        cell[1] = decay * cell[1] + float(value)
            for target in range(self.width):
                def contrast(source):
                    index = source * self.width + target
                    return abs(self._prob(self.fast[index][context], 1) -
                               self._prob(self.fast[index][context], 0))
                source = max(range(self.width), key=contrast)
                index = source * self.width + target
                state = int(self.previous[source])
                fast_cell = self.fast[index][context]
                slow_cell = self.slow[index][context]
                fast_mass = sum(item[0] for item in fast_cell)
                slow_mass = sum(item[0] for item in slow_cell)
                total = fast_mass + slow_mass + 1.0
                prediction[target] = ((fast_mass * self._prob(fast_cell, state) +
                                       slow_mass * self._prob(slow_cell, state)) / total)
                self.edges += (target >= self.width / 2 and source < self.width / 2) * abs(
                    self._prob(fast_cell, 1) - self._prob(fast_cell, 0))
        self.previous = list(observation)
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * int(PARAMS["contexts"]) * 64}
