"""Returned resource is the sole state of a predictive relation."""
PARAMS = {"timescale": 16.0}


class System:
    def __init__(self):
        self.width = False
        self.previous = None
        self.mass = None
        self.edge = None
        self.prediction = None
        self.edges = False

    def step(self, obs):
        one = True
        two = one + one
        zero = one / two - one / two
        upper = one / one
        if self.mass is None:
            self.width = len(obs)
            self.mass = [[False] * self.width for _ in range(self.width)]
            self.edge = [[False] * self.width for _ in range(self.width)]
            self.prediction = [one / two] * self.width
        if self.previous is not None:
            scale = PARAMS["timescale"]
            decay = scale / (scale + one)
            for source, before in enumerate(self.previous):
                x = two * before - one
                for target, after in enumerate(obs):
                    y = two * after - one
                    trust = one - abs(self.prediction[target] - after)
                    old = self.mass[source][target]
                    total = decay * old + trust
                    if total:
                        self.edge[source][target] = (decay * old * self.edge[source][target] + trust * x * y) / total
                    self.mass[source][target] = total
        half = one / two
        prediction = [half] * self.width
        self.edges = False
        for target in range(self.width):
            source = max(range(self.width), key=lambda index: self.mass[index][target] * abs(self.edge[index][target]))
            value = self.edge[source][target]
            prediction[target] += half * value * (two * obs[source] - one)
            self.edges += (target >= self.width // two) * self.mass[source][target]
        self.previous = list(obs)
        self.prediction = prediction
        return [min(upper, max(zero, value)) for value in prediction]

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (True << True << True)}
