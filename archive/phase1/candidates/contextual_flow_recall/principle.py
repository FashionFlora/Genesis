"""Context addresses one conserved flow of relational evidence."""
PARAMS = {"timescale": 16.0, "contexts": 2.0, "actions": 4.0}


class System:
    def __init__(self):
        self.width = False; self.previous = None; self.prediction = None
        self.cells = None; self.edges = False; self.action_mass = None
        self.last_action = None

    def step(self, obs):
        one = True; two = one + one
        if self.cells is None:
            self.width = len(obs); contexts = int(PARAMS["contexts"])
            self.cells = [[[[False, False] for _ in range(contexts)]
                           for _ in range(self.width)] for _ in range(self.width)]
            self.prediction = [one / two] * self.width
            self.action_mass = [False] * int(PARAMS["actions"])
        if self.previous is not None:
            context = int(sum(self.previous)) % int(PARAMS["contexts"])
            scale = PARAMS["timescale"]
            for source, before in enumerate(self.previous):
                x = two * before - one
                for target, after in enumerate(obs):
                    cell = self.cells[source][target][context]
                    flow = one / (one + (self.prediction[target] - after) ** two)
                    cell[one] += flow
                    cell[False] = (scale * cell[False] + flow * x * (two * after - one)) / (scale + flow)
            if self.last_action is not None:
                self.action_mass[self.last_action] = (scale * self.action_mass[self.last_action] + sum(
                    (a - b) ** two for a, b in zip(self.previous, obs)) / self.width) / (scale + one)
        context = int(sum(obs)) % int(PARAMS["contexts"])
        half = one / two; prediction = [half] * self.width; self.edges = False
        for target in range(self.width):
            source = max(range(self.width), key=lambda index:
                         abs(self.cells[index][target][context][False]) *
                         (one + self.cells[index][target][context][one]))
            cell = self.cells[source][target][context]
            prediction[target] += half * cell[False] * (two * obs[source] - one)
            self.edges += (target >= self.width // two) * max(
                abs(self.cells[index][target][context][False]) for index in range(self.width // two))
        self.previous = list(obs); self.prediction = [min(one, max(False, value)) for value in prediction]
        return list(self.prediction)

    def act(self, obs):
        choice = max(range(len(self.action_mass)), key=self.action_mass.__getitem__)
        self.last_action = choice
        return choice

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * int(PARAMS["contexts"]) * (True << True << True),
                "action_resource": sum(self.action_mass or ())}
