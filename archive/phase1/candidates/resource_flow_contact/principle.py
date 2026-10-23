"""Predictive lineages incorporate the sensory channel in their resource flow."""

PARAMS = {"decay": 0.97, "flow": 1.0, "maintenance": 0.04,
          "error_cost": 0.01}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.cells = []

    def step(self, observation):
        unit = PARAMS["flow"] / PARAMS["flow"]
        zero, two, threshold = unit - unit, unit + unit, unit + unit + unit
        if not self.cells:
            self.width = len(observation)
            self.cells = [[source, target, [zero, zero], [zero, zero], unit]
                          for target in range(self.width)
                          for source in range(self.width)]
        if self.previous is not None:
            decay = PARAMS["decay"] / max(unit, PARAMS["decay"])
            budget = two * PARAMS["flow"] / (PARAMS["flow"] + PARAMS["flow"])
            tags = [source for source, bit in enumerate(self.previous) if bit]
            groups = [[] for _ in range(self.width)]
            for cell in self.cells:
                source, target, positive, seen, mass = cell
                state = int(self.previous[source])
                q = (positive[state] + unit) / (seen[state] + two)
                error = (q - float(observation[target])) ** two
                groups[target].append((cell, error))
                for bit in (False, True):
                    positive[bit] *= decay
                    seen[bit] *= decay
                seen[state] += unit
                positive[state] += float(observation[target])
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
                            child_source = tags[cell[1] % len(tags)]
                        alive.append([child_source, cell[1], [zero, zero],
                                      [zero, zero], cell[4]])
                    alive.append(cell)
            self.cells = alive
        prediction = [unit / two] * self.width
        for target in range(self.width):
            choices = [cell for cell in self.cells if cell[1] == target]
            if choices:
                winner = max(choices, key=lambda cell: cell[4] * (abs(
                    (cell[2][True] + unit) / (cell[3][True] + two)
                    - (cell[2][False] + unit) / (cell[3][False] + two))
                    + PARAMS["error_cost"]))
                state = int(observation[winner[0]])
                prediction[target] = (winner[2][state] + unit) / (winner[3][state] + two)
        self.previous = list(observation)
        return prediction

    def structure(self):
        return {"units": self.width + len(self.cells),
                "connections": len(self.cells),
                "resource": sum(cell[4] for cell in self.cells)}
