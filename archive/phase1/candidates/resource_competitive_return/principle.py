"""A conserved predictive return funds both relation memory and selection."""


class System:
    def __init__(self):
        self.width = False
        self.previous = None
        self.evidence = None
        self.mass = None
        self.edges = False

    def step(self, obs):
        one = True
        two = one + one
        half = one / two
        if self.evidence is None:
            self.width = len(obs)
            self.evidence = [[False] * self.width for _ in range(self.width)]
            self.mass = [[one / self.width] * self.width for _ in range(self.width)]
        if self.previous is not None:
            for target, after in enumerate(obs):
                returned = []
                for source, before in enumerate(self.previous):
                    x = two * before - one
                    y = two * after - one
                    prediction = half + half * self.evidence[source][target] * x
                    returned.append(one / (one + (prediction - after) ** two))
                total = sum(self.mass[source][target] * returned[source]
                            for source in range(self.width))
                for source, before in enumerate(self.previous):
                    share = self.mass[source][target] * returned[source] / total
                    self.evidence[source][target] += share * (
                        (two * before - one) * (two * after - one) -
                        self.evidence[source][target])
                    self.mass[source][target] = share
        prediction = [half] * self.width
        self.edges = False
        for target in range(self.width):
            support = [self.mass[source][target] * abs(self.evidence[source][target])
                       for source in range(self.width)]
            self.edges += (target >= self.width // two) * sum(support)
            prediction[target] += half * sum(
                self.mass[source][target] * self.evidence[source][target] *
                (two * obs[source] - one) for source in range(self.width))
        self.previous = list(obs)
        return [min(1.0, max(0.0, value)) for value in prediction]

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (True << True << True)}
