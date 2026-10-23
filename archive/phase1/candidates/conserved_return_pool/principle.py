"""A target conserves returned predictive flow across competing relations."""
PARAMS = {"timescale": 16.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.cells = None
        self.edges = 0.0

    def step(self, obs):
        half = 0.5
        if self.cells is None:
            self.width = len(obs)
            self.cells = [[[0.0, 0.0] for _ in range(self.width)]
                          for _ in range(self.width)]

        if self.previous is not None:
            scale = PARAMS["timescale"]
            old = self.previous
            for target, after in enumerate(obs):
                y = 2.0 * after - 1.0
                returns = []
                for source, before in enumerate(old):
                    x = 2.0 * before - 1.0
                    corr, mass = self.cells[source][target]
                    local_prediction = half + half * corr * x
                    returns.append(1.0 / (1.0 + (local_prediction - after) ** 2))
                total = sum(returns)
                for source, before in enumerate(old):
                    x = 2.0 * before - 1.0
                    cell = self.cells[source][target]
                    share = returns[source] / total
                    cell[0] = (scale * cell[0] + share * x * y) / (scale + share)
                    cell[1] = (scale * cell[1] + share) / (scale + 1.0)

        prediction = [half] * self.width
        self.edges = 0.0
        for target in range(self.width):
            source = max(range(self.width),
                         key=lambda i: self.cells[i][target][1] * abs(self.cells[i][target][0]))
            corr = self.cells[source][target][0]
            prediction[target] += half * corr * (2.0 * obs[source] - 1.0)
            self.edges += (target >= self.width // 2) * max(
                (self.cells[i][target][1] for i in range(self.width // 2)), default=0.0)

        self.previous = list(obs)
        return [min(1.0, max(0.0, value)) for value in prediction]

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * 16}
