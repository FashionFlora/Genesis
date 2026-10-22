"""Prototype: local resource competition among predictive edge cells."""

PARAMS = {"decay": 0.97, "flow": 1.0, "maintenance": 0.04,
          "error_cost": 0.01, "fission": 3.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.cells = []

    def step(self, obs):
        if not self.cells:
            self.width = len(obs)
            self.cells = [[source, target, [0.0, 0.0], [0.0, 0.0], 1.0]
                          for target in range(self.width)
                          for source in range(self.width)]
        if self.previous is not None:
            grouped = [[] for _ in range(self.width)]
            errors = []
            for cell in self.cells:
                source, target, positive, seen, mass = cell
                state = int(self.previous[source])
                q = (positive[state] + 1.0) / (seen[state] + 2.0)
                error = (q - float(obs[target])) ** 2
                errors.append(error)
                grouped[target].append((cell, error))
                for bit in range(2):
                    positive[bit] *= PARAMS["decay"]
                    seen[bit] *= PARAMS["decay"]
                seen[state] += 1.0
                positive[state] += float(obs[target])
            survivors = []
            for target_group in grouped:
                total = sum(1.0 / (1.0 + error) for _cell, error in target_group)
                for cell, error in target_group:
                    intake = PARAMS["flow"] * (1.0 / (1.0 + error)) / total
                    cell[4] += intake - PARAMS["maintenance"] - PARAMS["error_cost"] * error
                    if cell[4] <= 0.0:
                        continue
                    while cell[4] >= PARAMS["fission"]:
                        cell[4] *= 0.5
                        child = [cell[0], cell[1], cell[2].copy(), cell[3].copy(), cell[4]]
                        survivors.append(child)
                    survivors.append(cell)
            self.cells = survivors
        result = [0.5] * self.width
        for target in range(self.width):
            options = [cell for cell in self.cells if cell[1] == target]
            if options:
                winner = max(options, key=lambda cell:
                             abs((cell[2][1] + 1.0) / (cell[3][1] + 2.0) -
                                 (cell[2][0] + 1.0) / (cell[3][0] + 2.0)))
                state = int(obs[winner[0]])
                result[target] = (winner[2][state] + 1.0) / (winner[3][state] + 2.0)
        self.previous = list(obs)
        return result

    def structure(self):
        return {"units": self.width + len(self.cells),
                "connections": len(self.cells),
                "memory_bytes": len(self.cells) * 48 + self.width * 16,
                "resource": sum(cell[4] for cell in self.cells)}
