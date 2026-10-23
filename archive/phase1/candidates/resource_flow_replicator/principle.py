"""Returned local flow jointly updates a relation and its persistence mass."""
PARAMS = {"timescale": 16.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.relations = None
        self.mass = None
        self.edges = 0.0

    def step(self, obs):
        one = True
        two = one + one
        half = one / two
        if self.relations is None:
            self.width = len(obs)
            self.relations = [[0.0] * self.width for _ in range(self.width)]
            self.mass = [[half] * self.width for _ in range(self.width)]
        if self.previous is not None:
            scale = PARAMS["timescale"]
            for source, before in enumerate(self.previous):
                x = two * before - one
                for target, after in enumerate(obs):
                    value = half + half * self.relations[source][target] * x
                    flow = one / (one + (value - after) ** two)
                    self.mass[source][target] = (scale * self.mass[source][target] + flow) / (scale + one)
                    sample = x * (two * after - one)
                    self.relations[source][target] = (scale * self.relations[source][target] + flow * sample) / (scale + flow)
        prediction = [half] * self.width
        self.edges = 0.0
        for target in range(self.width):
            source = max(range(self.width),
                         key=lambda index: self.mass[index][target] * abs(self.relations[index][target]))
            prediction[target] += half * self.relations[source][target] * (two * obs[source] - one)
            if target >= self.width // two:
                self.edges += self.mass[source][target] * abs(self.relations[source][target])
        self.previous = list(obs)
        return [min(one, max(half - half, value)) for value in prediction]

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (True << True << True)}
