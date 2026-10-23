"""A conserved target pool routes returned resource among source relations."""

PARAMS = {"timescale": 16.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.relations = None
        self.pool = None
        self.prediction = None
        self.edges = 0.0

    def step(self, obs):
        one = True
        two = one + one
        half = one / two
        zero = half - half
        if self.relations is None:
            self.width = len(obs)
            self.relations = [[zero] * self.width for _ in range(self.width)]
            self.pool = [[one / self.width] * self.width for _ in range(self.width)]
            self.prediction = [half] * self.width
        if self.previous is not None:
            scale = PARAMS["timescale"]
            returned = [[zero] * self.width for _ in range(self.width)]
            for source, before in enumerate(self.previous):
                x = two * before - one
                for target, after in enumerate(obs):
                    value = half + half * self.relations[source][target] * x
                    error = value - after
                    returned[source][target] = one / (one + error * error)
            for target in range(self.width):
                total = zero
                for source in range(self.width):
                    share = self.pool[source][target]
                    flow = returned[source][target]
                    total += share * flow
                total = max(total, one / (self.width * self.width))
                for source, before in enumerate(self.previous):
                    x = two * before - one
                    after = obs[target]
                    share = self.pool[source][target]
                    flow = returned[source][target]
                    share = share * flow / total
                    self.pool[source][target] = share
                    sample = x * (two * after - one)
                    self.relations[source][target] = (
                        scale * self.relations[source][target] + flow * sample
                    ) / (scale + flow)
        prediction = [half] * self.width
        self.edges = zero
        for target in range(self.width):
            source = max(range(self.width),
                         key=lambda index: self.pool[index][target] *
                         abs(self.relations[index][target]))
            value = self.relations[source][target]
            prediction[target] += half * value * (two * obs[source] - one)
            if target >= self.width // two:
                self.edges += self.pool[source][target] * abs(value)
        self.previous = list(obs)
        self.prediction = prediction
        return [min(one, max(half - half, value)) for value in prediction]

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (True << True << True)}
