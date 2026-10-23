"""One returned edge flow supplies prediction, persistence, and action."""
PARAMS = {"timescale": 16.0, "decay": 0.97}


class System:
    def __init__(self):
        self.width = False; self.previous = None; self.cells = None
        self.prediction = None; self.edges = False
        self.action_mass = [False] * (True + True + True + True)
        self.last_target = False; self.last_action = False

    def step(self, obs):
        one = True; two = one + one
        if self.previous is None:
            self.width = len(obs); self.previous = list(obs)
            self.prediction = [one / two] * self.width
            return list(self.prediction)
        if self.cells is None:
            self.cells = [[[False, False] for _ in range(self.width)]
                          for _ in range(self.width)]
        scale = PARAMS["timescale"]
        for source, before in enumerate(self.previous):
            x = two * before - one
            for target, after in enumerate(obs):
                y = two * after - one; cell = self.cells[source][target]
                flow = one / (one + (self.prediction[target] - after) ** two)
                cell[one] += flow; cell[False] = (scale * cell[False] + x * y) / (scale + one)
        half = one / two; prediction = [half] * self.width; self.edges = False
        for target in range(self.width):
            source = max(range(self.width), key=lambda index: abs(self.cells[index][target][False]) *
                         (one + self.cells[index][target][one]))
            value = self.cells[source][target][False]
            prediction[target] += half * value * (two * obs[source] - one)
            self.edges += (target >= self.width // two) * max(
                abs(self.cells[index][target][False]) for index in range(self.width // two))
        self.previous = list(obs); self.prediction = prediction
        return [min(one, max(False, value)) for value in prediction]

    def act(self, obs):
        one = True; two = one + one; four = two + two; seven = four + two + one
        cells = max(one, len(obs) // seven)
        address = sum((index + one) * value for index, value in enumerate(obs))
        hit = float(address % cells == self.last_target)
        self.action_mass = [PARAMS["decay"] * mass + hit * float(action == self.last_action)
                            for action, mass in enumerate(self.action_mass)]
        choice = max(range(four), key=lambda action: self.action_mass[action] +
                     float((address + action) % four == False))
        self.last_action = choice; self.last_target = (address + choice) % cells
        return choice

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (True << True << True),
                "action_resource": sum(self.action_mass)}
