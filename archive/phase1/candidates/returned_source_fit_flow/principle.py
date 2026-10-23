"""Each relation retains and learns in proportion to its own predictive return."""
PARAMS = {"timescale": 16.0}


class System:
    def __init__(self):
        self.width = False
        self.previous = None
        self.cells = None
        self.prediction = None
        self.edges = False
        self.action_mass = [0.0] * 4
        self.action_count = [0] * 4
        self.previous_action = None

    def step(self, obs):
        one = True
        two = one + one
        half = one / two
        if self.previous_action is not None and self.prediction is not None:
            error = sum((pred - value) ** two for pred, value in zip(self.prediction, obs)) / len(obs)
            action = self.previous_action
            self.action_mass[action] += one / (one + error)
            self.action_count[action] += 1
        if self.cells is None:
            self.width = len(obs)
            self.cells = [[[False, False] for _ in range(self.width)]
                          for _ in range(self.width)]
            self.prediction = [half] * self.width
        if self.previous is not None:
            scale = PARAMS["timescale"]
            for source, before in enumerate(self.previous):
                x = two * before - one
                for target, after in enumerate(obs):
                    cell = self.cells[source][target]
                    edge_prediction = half + half * cell[False] * x
                    flow = one / (one + (edge_prediction - after) ** two)
                    cell[one] = (scale * cell[one] + flow) / (scale + one)
                    cell[False] = (scale * cell[False] + flow * x * (two * after - one)) / (scale + flow)
        prediction = [half] * self.width
        self.edges = False
        for target in range(self.width):
            source = max(range(self.width), key=lambda index:
                         abs(self.cells[index][target][False]) *
                         (one + self.cells[index][target][one]))
            value = self.cells[source][target][False]
            prediction[target] += half * value * (two * obs[source] - one)
            self.edges += (target >= self.width // two) * max(
                abs(self.cells[index][target][False]) for index in range(self.width // two))
        self.previous = list(obs)
        self.prediction = prediction
        return [min(one, max(False, value)) for value in prediction]

    def act(self, obs):
        action = max(range(4), key=lambda index:
                     (float("inf") if self.action_count[index] == 0 else
                      self.action_mass[index] / self.action_count[index]))
        self.previous_action = action
        return action

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (True << True << True)}
