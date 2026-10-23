"""A process learns only from the predictive resource flow it receives."""

PARAMS = {"decay": 0.97, "flow": 2.4, "maintenance": 0.04,
          "error_cost": 0.01}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.cells = []

    def step(self, observation):
        unit = PARAMS["flow"] / PARAMS["flow"]
        zero, two, threshold = unit - unit, unit + unit, unit + unit + unit
        decay = min(PARAMS["decay"], unit)
        if not self.cells:
            self.width = len(observation)
            self.cells = [[source, target, [zero, zero], [zero, zero], unit]
                          for target in range(self.width)
                          for source in range(self.width)]
        if self.previous is not None:
            groups = [[] for _ in range(self.width)]
            for cell in self.cells:
                source, target, positive, seen, mass = cell
                state = int(self.previous[source])
                q = (positive[state] + unit) / (seen[state] + two)
                error = (q - float(observation[target])) ** two
                groups[target].append((cell, error, state))
            alive = []
            for group in groups:
                normalizer = sum(unit / (unit + error)
                                 for _cell, error, _state in group)
                for cell, error, state in group:
                    source, target, positive, seen, mass = cell
                    share = unit / (unit + error) / normalizer
                    flow = PARAMS["flow"] * share
                    retention = decay ** (unit / max(mass, unit))
                    for bit in (False, True):
                        positive[bit] *= retention
                        seen[bit] *= retention
                    seen[state] += flow
                    positive[state] += flow * float(observation[target])
                    cell[4] += (flow - PARAMS["maintenance"]
                                - PARAMS["error_cost"] * error)
                    if cell[4] <= zero:
                        continue
                    while cell[4] >= threshold:
                        cell[4] *= unit / two
                        alive.append([source, target, positive.copy(),
                                      seen.copy(), cell[4]])
                    alive.append(cell)
            self.cells = alive
        prediction = [unit / two] * self.width
        for target in range(self.width):
            choices = [cell for cell in self.cells if cell[1] == target]
            if choices:
                cell = max(choices, key=lambda item: item[4] * (abs(
                    (item[2][1] + unit) / (item[3][1] + two)
                    - (item[2][0] + unit) / (item[3][0] + two))
                    + PARAMS["error_cost"]))
                state = int(observation[cell[0]])
                prediction[target] = ((cell[2][state] + unit)
                                      / (cell[3][state] + two))
        self.previous = list(observation)
        return prediction

    def structure(self):
        return {"units": self.width + len(self.cells),
                "connections": len(self.cells),
                "resource": sum(cell[4] for cell in self.cells)}
