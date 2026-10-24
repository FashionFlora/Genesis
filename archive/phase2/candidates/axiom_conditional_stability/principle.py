"""Relations persist when their conditional predictions remain useful."""

PARAMS = {"base": 0.97, "shock": 0.35, "floor": 0.55, "support": 4.0}


class System:
    def __init__(self):
        self.previous = self.prediction = self.table = None
        self.mass = 0

    def step(self, obs):
        n = len(obs)
        if self.table is None:
            self.table = [[[[0.0, 0.0] for _ in range(2)] for _ in range(n)] for _ in range(n)]
        errors = [0.5] * n if self.prediction is None else [abs(float(x) - p) for x, p in zip(obs, self.prediction)]
        for i, row in enumerate(self.table):
            for j, pair in enumerate(row):
                decay = max(PARAMS["floor"], PARAMS["base"] - PARAMS["shock"] * max(0.0, errors[j] - 0.1))
                for cell in pair:
                    cell[0] *= decay
                    cell[1] *= decay
                if self.previous is not None:
                    cell = pair[self.previous[i]]
                    cell[0] += 1.0
                    cell[1] += float(obs[j])
        out, active = [], 0
        for j in range(n):
            pairs = [self.table[i][j] for i in range(n)]
            strength = [abs((b[1] + 1) / (b[0] + 2) - (a[1] + 1) / (a[0] + 2)) * (a[0] + b[0]) / (a[0] + b[0] + PARAMS["support"]) for a, b in pairs]
            i = max(range(n), key=strength.__getitem__)
            a, b = pairs[i]
            if strength[i] > 0:
                out.append((b if obs[i] else a)[1] + 1)
                out[-1] /= (b if obs[i] else a)[0] + 2
                active += int(i != j and strength[i] > 0.2)
            else:
                out.append(0.5)
        self.mass = active
        self.previous, self.prediction = [int(x) for x in obs], out
        return out

    def structure(self):
        return {"units": self.mass, "connections": self.mass, "memory_bytes": len(self.table) ** 2 * 64 if self.table else 0}
