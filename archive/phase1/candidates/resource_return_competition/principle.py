"""One conserved target resource pool governs relation learning and use."""

PARAMS = {"turnover": 16.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.support = None
        self.mass = None
        self.edges = 0.0

    def step(self, obs):
        one, two = True, True + True
        half = one / two
        if self.support is None:
            self.width = len(obs)
            self.support = [[0.0] * self.width for _ in range(self.width)]
            self.mass = [[1.0 / self.width] * self.width
                         for _ in range(self.width)]

        if self.previous is not None:
            scale = PARAMS["turnover"]
            for target, after in enumerate(obs):
                returned = []
                for source, before in enumerate(self.previous):
                    x = two * before - one
                    y = two * after - one
                    old = self.support[source][target]
                    prediction = half + half * old * x
                    error = (prediction - after) ** two
                    flow = self.mass[source][target] / (one + error)
                    returned.append(flow)
                    self.support[source][target] = (
                        scale * old + flow * x * y) / (scale + flow)
                total = sum(returned)
                if total:
                    for source, flow in enumerate(returned):
                        self.mass[source][target] = flow / total

        prediction = [half] * self.width
        self.edges = 0.0
        for target in range(self.width):
            for source in range(self.width):
                prediction[target] += (half * self.mass[source][target]
                                       * self.support[source][target]
                                       * (two * obs[source] - one))
            self.edges += max(self.mass[source][target]
                              for source in range(self.width // two))
        self.previous = list(obs)
        return [min(one, max(False, value)) for value in prediction]

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * 16}
