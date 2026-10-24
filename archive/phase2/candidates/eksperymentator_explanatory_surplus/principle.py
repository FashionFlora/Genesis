"""Relations persist in proportion to their prequential gain over a target prior."""

import math

PARAMS = {"rate": 1.0, "decay": 0.95, "prior": 1.0}


class System:
    def __init__(self):
        self.previous = None
        self.base = None
        self.cells = None
        self.log_mass = None
        self.last_base = None
        self.last_conditional = None

    def step(self, obs):
        n = len(obs)
        if self.base is None:
            self.base = [[0.0, 0.0] for _ in range(n)]
            self.cells = [[[[0.0, 0.0] for _ in range(2)] for _ in range(n)]
                          for _ in range(n)]
            self.log_mass = [[0.0 for _ in range(n)] for _ in range(n)]

        baseline = []
        conditional = [[0.5 for _ in range(n)] for _ in range(n)]
        prediction = []
        for target in range(n):
            count, total = self.base[target]
            baseline.append((total + 0.5 * PARAMS["prior"]) /
                            (count + PARAMS["prior"]))
            weights = []
            for source in range(n):
                a, b = self.cells[source][target]
                state = int(obs[source])
                cell = (a, b)[state]
                conditional[source][target] = (
                    cell[1] + 0.5 * PARAMS["prior"]
                ) / (cell[0] + PARAMS["prior"])
                weights.append(self.log_mass[source][target])
            peak = max([0.0] + weights)
            norm = math.exp(-peak) + sum(math.exp(weight - peak) for weight in weights)
            mixed = math.exp(-peak) * baseline[-1]
            for source, weight in enumerate(weights):
                mixed += math.exp(weight - peak) * conditional[source][target]
            prediction.append(mixed / norm)

        if self.previous is not None:
            for target, value in enumerate(obs):
                y = float(value)
                error_base = (y - self.last_base[target]) ** 2
                for source in range(n):
                    error_cond = (y - self.last_conditional[source][target]) ** 2
                    self.log_mass[source][target] = (
                        PARAMS["decay"] * self.log_mass[source][target]
                        + PARAMS["rate"] * (error_base - error_cond)
                    )
            for target, value in enumerate(obs):
                cell = self.base[target]
                cell[0] = PARAMS["decay"] * cell[0] + 1.0
                cell[1] = PARAMS["decay"] * cell[1] + float(value)
                for source in range(n):
                    row = self.cells[source][target]
                    for entry in row:
                        entry[0] *= PARAMS["decay"]
                        entry[1] *= PARAMS["decay"]
                    entry = row[int(self.previous[source])]
                    entry[0] += 1.0
                    entry[1] += float(value)

        self.previous = [int(float(value) > 0.5) for value in obs]
        self.last_base = baseline
        self.last_conditional = conditional
        return prediction

    def structure(self):
        n = len(self.log_mass) if self.log_mass else 0
        active = sum(weight > 0.0 for row in self.log_mass for weight in row)
        return {"units": active, "connections": active,
                "memory_bytes": n * n * 5 * 8}
