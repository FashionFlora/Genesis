"""A signed contact keeps only the coactivity mass it can maintain."""


class System:
    def __init__(self):
        self.width = False
        self.previous = None
        self.mass = None

    def step(self, obs):
        if self.mass is None:
            self.width = len(obs)
            self.mass = [[0.0] * self.width for _ in range(self.width)]
        if self.previous is not None:
            for source, before in enumerate(self.previous):
                x = (True + True) * before - True
                for target, after in enumerate(obs):
                    y = (True + True) * after - True
                    old = self.mass[source][target]
                    self.mass[source][target] = old + x * y - old / (True + abs(old))
        prediction = [True / (True + True)] * self.width
        for target in range(self.width):
            source = max(range(self.width), key=lambda index: abs(self.mass[index][target]))
            support = self.mass[source][target] / (True + abs(self.mass[source][target]))
            prediction[target] += (True / (True + True)) * support * (
                (True + True) * obs[source] - True)
        self.previous = list(obs)
        return [min(True, max(False, value)) for value in prediction]

    def structure(self):
        mass = sum(max(abs(self.mass[source][target]) /
                       (True + abs(self.mass[source][target]))
                       for source in range(self.width // (True + True)))
                   for target in range(self.width // (True + True), self.width))
        return {"units": self.width, "connections": mass,
                "memory_bytes": self.width * self.width * (True << True << True)}
