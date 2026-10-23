"""Context selects among retained predictive-equivalence models."""

PARAMS = {"contexts": 8, "timescale": 8.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.banks = None
        self.selected = None
        self.edges = 0

    def _blank(self):
        return [[[[0.0, 0.0] for _ in range(2)] for _ in range(self.width)]
                for _ in range(self.width)]

    def _address(self, obs):
        return sum((index + 1) * int(bit)
                   for index, bit in enumerate(obs)) % int(PARAMS["contexts"])

    @staticmethod
    def _prob(cell):
        return (cell[1] + 1.0) / (cell[0] + 2.0)

    def step(self, obs):
        if self.banks is None:
            self.width = len(obs)
            self.banks = [self._blank(), self._blank()]
            self.selected = [0] * int(PARAMS["contexts"])
        address = self._address(self.previous) if self.previous is not None else 0
        if self.previous is not None:
            active = self.banks[self.selected[address]]
            dormant = self.banks[1 - self.selected[address]]
            retention = PARAMS["timescale"] / (PARAMS["timescale"] + 1.0)
            for source, state in enumerate(self.previous):
                bit = int(state)
                for target, value in enumerate(obs):
                    a = active[source][target][bit]
                    d = dormant[source][target][bit]
                    if (self._prob(d) - value) ** 2 < (self._prob(a) - value) ** 2:
                        self.selected[address] = 1 - self.selected[address]
                        active, dormant = dormant, active
                        a = active[source][target][bit]
                    a[0] = retention * a[0] + 1.0
                    a[1] = retention * a[1] + value

        prediction = [0.5] * self.width
        self.edges = 0
        active = self.banks[self.selected[address]]
        for target in range(self.width):
            source = max(range(self.width), key=lambda i: abs(
                self._prob(active[i][target][1]) - self._prob(active[i][target][0])))
            prediction[target] = self._prob(active[source][target][int(obs[source])])
            self.edges += (target >= self.width / 2) * (source < self.width / 2)
        self.previous = list(obs)
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * int(PARAMS["contexts"]) * 32}
