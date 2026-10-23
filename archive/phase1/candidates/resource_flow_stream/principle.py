"""Prediction is the weighted persistence of locally paid edge cells."""

PARAMS = {"decay": 0.90, "flow": 2.40, "maintenance": 0.01,
          "error_cost": 0.03, "fission": 2.00}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.cells = []

    def step(self, obs):
        if not self.cells:
            self.width = len(obs)
            self.cells = [[s, t, [1.0, 1.0], [2.0, 2.0], 1.0]
                          for t in range(self.width) for s in range(self.width)]
        if self.previous is not None:
            share = PARAMS["flow"] / max(1, self.width * self.width)
            alive = []
            for source, target, positive, seen, mass in self.cells:
                context, y = int(self.previous[source]), float(obs[target])
                q = (positive[context] + 1.0) / (seen[context] + 2.0)
                mass += share - PARAMS["maintenance"] - PARAMS["error_cost"] * (q - y) ** 2
                for k in range(2):
                    positive[k] *= PARAMS["decay"]
                    seen[k] *= PARAMS["decay"]
                seen[context] += 1.0
                positive[context] += y
                if mass > 0.0:
                    while mass >= PARAMS["fission"]:
                        mass *= 0.5
                        alive.append([source, target, positive.copy(), seen.copy(), mass])
                    alive.append([source, target, positive, seen, mass])
            self.cells = alive
        result = [0.5] * self.width
        for target in range(self.width):
            weighted = total = 0.0
            for source, edge, positive, seen, mass in self.cells:
                if edge == target:
                    q = (positive[int(obs[source])] + 1.0) / (seen[int(obs[source])] + 2.0)
                    weighted += mass * q
                    total += mass
            if total:
                result[target] = weighted / total
        self.previous = list(obs)
        return result

    def structure(self):
        return {"units": self.width + len(self.cells),
                "connections": len(self.cells),
                "memory_bytes": len(self.cells) * 48 + self.width * 16}
