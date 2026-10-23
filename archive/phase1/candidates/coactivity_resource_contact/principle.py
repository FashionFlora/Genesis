"""Predictive coactivity redistributes resource, which carries new contacts."""

PARAMS = {"decay": 0.97, "flow": 1.0, "maintenance": 0.04,
          "error_cost": 0.01}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.cells = []
        self.edges = 0

    def step(self, obs):
        unit = PARAMS["flow"] / PARAMS["flow"]
        zero, two = unit - unit, unit + unit
        threshold = unit * (unit + unit + unit)
        if not self.cells:
            self.width = len(obs)
            self.cells = [[source, target, [zero, zero], [zero, zero], unit]
                          for target in range(self.width)
                          for source in range(self.width)]
        if self.previous is not None:
            decay = PARAMS["decay"] / max(unit, PARAMS["decay"])
            budget = unit
            tags = [source for source, bit in enumerate(obs) if bit]
            groups = [[] for _ in range(self.width)]
            for cell in self.cells:
                source, target, positive, seen, mass = cell
                state = int(self.previous[source])
                q = (positive[state] + unit) / (seen[state] + two)
                error = (q - float(obs[target])) ** two
                groups[target].append((cell, error))
                for bit in (False, True):
                    positive[bit] *= decay
                    seen[bit] *= decay
                seen[state] += unit
                positive[state] += float(obs[target])
            alive = []
            for group in groups:
                normalizer = sum(unit / (unit + error) for _cell, error in group)
                for cell, error in group:
                    cell[4] += (budget * unit / (unit + error) / normalizer
                                - PARAMS["maintenance"]
                                - PARAMS["error_cost"] * error)
                    if cell[4] <= zero:
                        continue
                    while cell[4] >= threshold:
                        cell[4] *= unit / two
                        child_source = cell[0]
                        if tags:
                            child_source = tags[(cell[0] + cell[1]) % len(tags)]
                        alive.append([child_source, cell[1], [zero, zero],
                                      [zero, zero], cell[4]])
                    alive.append(cell)
            self.cells = alive
        prediction = [unit / two] * self.width
        self.edges = 0
        for target in range(self.width):
            choices = [cell for cell in self.cells if cell[1] == target]
            if choices:
                def gap(cell):
                    positive, seen = cell[2], cell[3]
                    return abs((positive[True] + unit) / (seen[True] + two)
                               - (positive[False] + unit) / (seen[False] + two))
                winner = max(choices, key=lambda cell: cell[4] * gap(cell))
                self.edges += int(target >= self.width // two
                                  and winner[0] < self.width // two)
                state = int(obs[winner[0]])
                prediction[target] = (winner[2][state] + unit) / (winner[3][state] + two)
        self.previous = list(obs)
        return prediction

    def structure(self):
        return {"units": self.width + len(self.cells), "connections": self.edges,
                "resource": sum(cell[4] for cell in self.cells)}
