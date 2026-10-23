"""A relation survives exactly while it reduces local prediction error."""

PARAMS = {"decay": 0.97}


class System:
    def __init__(self):
        self.n = 0
        self.last = None
        self.c = []
        self.edges = 0

    def step(self, obs):
        if not self.c:
            self.n = len(obs)
            self.c = [[[[0.0, 0.0] for _ in range(2)]
                       for _ in range(self.n)] for _ in range(self.n)]
        if self.last is not None:
            d = min(1.0, PARAMS["decay"])
            for i, bit in enumerate(map(int, self.last)):
                for j, value in enumerate(obs):
                    cell = self.c[i][j][bit]
                    cell[0] = d * cell[0] + 1.0
                    cell[1] = d * cell[1] + value
        out = []
        self.edges = 0
        for j in range(self.n):
            scores = [abs((self.c[i][j][1][1] + 1.0) /
                          (self.c[i][j][1][0] + 2.0) -
                          (self.c[i][j][0][1] + 1.0) /
                          (self.c[i][j][0][0] + 2.0))
                      for i in range(self.n)]
            i = max(range(self.n), key=scores.__getitem__)
            self.edges += i < self.n // 2 <= j
            cell = self.c[i][j][int(obs[i])]
            out.append((cell[1] + 1.0) / (cell[0] + 2.0))
        self.last = list(obs)
        return out

    def structure(self):
        return {"units": self.n, "connections": self.edges,
                "memory_bytes": self.n * self.n * 16}
