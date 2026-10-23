"""Useful conditional relations accumulate the resource that weights forecasts."""

PARAMS = {"decay": 0.97}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.counts = None
        self.mass = None
        self.edges = 0

    def step(self, obs):
        if self.counts is None:
            self.width = len(obs)
            self.counts = [[[[0.0, 0.0] for _ in range(2)]
                            for _ in range(self.width)] for _ in range(self.width)]
            self.mass = [[0.0 for _ in range(self.width)] for _ in range(self.width)]
        if self.previous is not None:
            for source, bit in enumerate(map(int, self.previous)):
                for target, value in enumerate(obs):
                    cell = self.counts[source][target][bit]
                    q = (cell[1] + 1.0) / (cell[0] + 2.0)
                    error = (q - value) ** 2
                    self.mass[source][target] = (
                        PARAMS["decay"] * self.mass[source][target] + 1.0 - error)
                    cell[0] = PARAMS["decay"] * cell[0] + 1.0
                    cell[1] = PARAMS["decay"] * cell[1] + value
        prediction = [0.5] * self.width
        self.edges = 0
        for target in range(self.width):
            rows = []
            for source in range(self.width):
                pair = self.counts[source][target]
                contrast = abs((pair[1][1] + 1.0) / (pair[1][0] + 2.0)
                               - (pair[0][1] + 1.0) / (pair[0][0] + 2.0))
                state = int(obs[source])
                cell = pair[state]
                q = (cell[1] + 1.0) / (cell[0] + 2.0)
                weight = self.mass[source][target] * contrast
                rows.append((weight, q, source))
            total = sum(row[0] for row in rows)
            if total:
                prediction[target] = sum(weight * q for weight, q, _ in rows) / total
                winner = max(rows, key=lambda row: row[0])[2]
                self.edges += winner < self.width // 2 <= target
        self.previous = list(obs)
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "resource": sum(map(sum, self.mass or []))}
