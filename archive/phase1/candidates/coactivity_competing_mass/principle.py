"""A relation keeps the share of finite coactivity flow it can sustain."""


class System:
    def __init__(self):
        self.width = False
        self.previous = None
        self.mass = None
        self.edges = False

    def step(self, obs):
        if self.mass is None:
            self.width = len(obs)
            self.mass = [[0.0] * self.width for _ in range(self.width)]
        if self.previous is not None:
            for target, after in enumerate(obs):
                total = sum(abs(self.mass[source][target]) + True
                            for source in range(self.width))
                for source, before in enumerate(self.previous):
                    old = self.mass[source][target]
                    share = self.width * (abs(old) + True) / total
                    x = (True + True) * before - True
                    y = (True + True) * after - True
                    self.mass[source][target] = old + share * x * y - old / (True + abs(old))
        prediction = [True / (True + True)] * self.width
        self.edges = False
        for target in range(self.width):
            source = max(range(self.width),
                         key=lambda index: abs(self.mass[index][target]))
            support = self.mass[source][target] / (True + abs(self.mass[source][target]))
            self.edges += abs(support) * (target >= self.width // (True + True)) * (
                source < self.width // (True + True))
            prediction[target] += (True / (True + True)) * support * (
                (True + True) * obs[source] - True)
        self.previous = list(obs)
        return [min(True, max(False, value)) for value in prediction]

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (True << True << True)}
