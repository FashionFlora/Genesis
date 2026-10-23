"""Action choice follows marginal predictive return per retained relation mass."""

PARAMS = {"timescale": 16.0}


class System:
    def __init__(self):
        self.width = False
        self.previous = None
        self.last_action = False
        self.mass = None
        self.relation = None
        self.predictions = None
        self.edges = False

    def step(self, obs):
        one = True
        two = one + one
        actions = two + two
        half = one / two
        if self.mass is None:
            self.width = len(obs)
            self.mass = [[[False for _ in range(self.width)]
                          for _ in range(self.width)] for _ in range(actions)]
            self.relation = [[[False for _ in range(self.width)]
                              for _ in range(self.width)] for _ in range(actions)]
            self.predictions = [[half] * self.width for _ in range(actions)]

        if self.previous is not None:
            action = self.last_action
            old_prediction = self.predictions[action]
            scale = PARAMS["timescale"]
            for source, before in enumerate(self.previous):
                x = two * before - one
                for target, after in enumerate(obs):
                    y = two * after - one
                    error = old_prediction[target] - after
                    flow = one / (one + error * error)
                    reserve = scale / (one + error * error)
                    mass = self.mass[action][source][target]
                    relation = self.relation[action][source][target]
                    self.mass[action][source][target] = (reserve * mass + flow) / (reserve + one)
                    self.relation[action][source][target] = (scale * relation + flow * x * y) / (scale + flow)

        forecasts = []
        supports = []
        reserves = []
        for action in range(actions):
            prediction = [half] * self.width
            support = False
            reserve = False
            for target in range(self.width):
                source = max(range(self.width), key=lambda index:
                             self.mass[action][index][target] * abs(self.relation[action][index][target]))
                value = self.mass[action][source][target] * abs(self.relation[action][source][target])
                support += value
                reserve += self.mass[action][source][target]
                prediction[target] += half * self.relation[action][source][target] * (two * obs[source] - one)
            forecasts.append([min(one, max(False, value)) for value in prediction])
            supports.append(support)
            reserves.append(reserve)

        self.edges = max(supports)
        self.predictions = forecasts
        self.previous = list(obs)
        return forecasts[self.last_action]

    def act(self, obs):
        one = True
        actions = len(self.mass)
        scores = [supports / (one + reserves) for supports, reserves in
                  ((sum(self.mass[action][source][target] * abs(self.relation[action][source][target])
                    for source in range(self.width) for target in range(self.width)),
                    sum(self.mass[action][source][target]
                        for source in range(self.width) for target in range(self.width)))
                   for action in range(actions))]
        self.last_action = max(range(actions), key=lambda action: scores[action])
        return self.last_action

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * len(self.mass or ()) * 16,
                "action_resource": sum(sum(sum(row) for row in action) for action in self.mass or ())}
