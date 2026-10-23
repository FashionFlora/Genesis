"""A local resource packet is selected by the preceding source-target transition."""

PARAMS = {"decay": 0.90, "dormant_decay": 0.995, "flow": 2.40,
          "maintenance": 0.01, "error_cost": 0.03, "fission": 2.00}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.cells = []

    def step(self, obs):
        if not self.cells:
            self.width = len(obs)
            self.cells = [[s, t, [1.0] * 4, [2.0] * 4, [1.0] * 4]
                          for t in range(self.width) for s in range(self.width)]
        if self.previous is not None:
            share = PARAMS["flow"] / max(1, self.width * self.width)
            alive = []
            for source, target, positive, seen, mass in self.cells:
                context = 2 * int(self.previous[source]) + int(self.previous[target])
                estimate = (positive[context] + 1.0) / (seen[context] + 2.0)
                error = (estimate - float(obs[target])) ** 2
                for index in range(4):
                    rate = PARAMS["decay"] if index == context else PARAMS["dormant_decay"]
                    positive[index] *= rate
                    seen[index] *= rate
                    mass[index] *= rate
                seen[context] += 1.0
                positive[context] += float(obs[target])
                mass[context] += share - PARAMS["maintenance"] - PARAMS["error_cost"] * error
                if sum(mass) > 0.0:
                    while mass[context] >= PARAMS["fission"]:
                        mass[context] *= 0.5
                        alive.append([source, target, positive.copy(), seen.copy(), mass.copy()])
                    alive.append([source, target, positive, seen, mass])
            self.cells = alive
        result = [0.5] * self.width
        for target in range(self.width):
            weighted = total = 0.0
            for source, edge, positive, seen, mass in self.cells:
                if edge == target:
                    context = 2 * int(self.previous[source]) + int(self.previous[target]) if self.previous is not None else 0
                    weight = mass[context]
                    estimate = (positive[context] + 1.0) / (seen[context] + 2.0)
                    weighted += weight * estimate
                    total += weight
            if total:
                result[target] = weighted / total
        self.previous = list(obs)
        return result

    def structure(self):
        return {"units": self.width + len(self.cells),
                "connections": len(self.cells),
                "memory_bytes": len(self.cells) * 80 + self.width * 16}
