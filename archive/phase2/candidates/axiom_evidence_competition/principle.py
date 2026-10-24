"""Relations share persistence and prediction in proportion to evidence."""

PARAMS = {"base": 0.97, "shock": 0.35, "floor": 0.55,
          "support": 4.0, "prior": 2.0, "threshold": 0.08}


class System:
    def __init__(self):
        self.previous = None
        self.prediction = None
        self.table = None
        self.means = None
        self.mass = 0

    def step(self, obs):
        n = len(obs)
        if self.table is None:
            self.table = [[[[0.0, 0.0] for _ in range(2)] for _ in range(n)]
                          for _ in range(n)]
            self.means = [[0.0, 0.0] for _ in range(n)]
        errors = [0.5] * n if self.prediction is None else [
            abs(float(value) - guess) for value, guess in zip(obs, self.prediction)]
        for target in range(n):
            decay = max(PARAMS["floor"], PARAMS["base"] -
                        PARAMS["shock"] * max(0.0, errors[target] - 0.1))
            mean = self.means[target]
            mean[0] *= decay
            mean[1] *= decay
            if self.previous is not None:
                mean[0] += 1.0
                mean[1] += float(obs[target])
            for source in range(n):
                for cell in self.table[source][target]:
                    cell[0] *= decay
                    cell[1] *= decay
                if self.previous is not None:
                    cell = self.table[source][target][self.previous[source]]
                    cell[0] += 1.0
                    cell[1] += float(obs[target])
        out = []
        active = 0
        for target in range(n):
            mean = self.means[target]
            total = mean[0] + PARAMS["prior"]
            estimate = (mean[1] + 0.5 * PARAMS["prior"]) / total
            strongest = 0.0
            for source in range(n):
                pair = self.table[source][target]
                a, b = pair
                p0 = (a[1] + 0.5) / (a[0] + 1.0)
                p1 = (b[1] + 0.5) / (b[0] + 1.0)
                evidence = abs(p1 - p0) * (a[0] + b[0]) / (
                    a[0] + b[0] + PARAMS["support"])
                cell = pair[self.previous[source]] if self.previous is not None else a
                forecast = (cell[1] + 0.5) / (cell[0] + 1.0)
                estimate = (estimate * total + evidence * forecast) / (total + evidence)
                total += evidence
                strongest = max(strongest, evidence)
            out.append(estimate)
            active += int(strongest > PARAMS["threshold"])
        self.mass = active
        self.previous = [int(float(value) > 0.5) for value in obs]
        self.prediction = out
        return out

    def structure(self):
        n = len(self.table) if self.table else 0
        return {"units": self.mass, "connections": self.mass,
                "memory_bytes": n * n * 64 if self.table else 0}
