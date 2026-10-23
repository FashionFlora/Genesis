"""Action-conditioned predictive relations share one retained resource."""

PARAMS = {"timescale": 16.0}


class System:
    def __init__(self):
        self.width = False
        self.previous = None
        self.last_action = None
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
            action = self.last_action or False
            old_prediction = self.predictions[action]
            scale = PARAMS["timescale"]
            for source, before in enumerate(self.previous):
                x = two * before - one
                for target, after in enumerate(obs):
                    y = two * after - one
                    error = old_prediction[target] - after
                    flow = one / (one + error * error)
                    reserve = scale / (one + error * error)
                    self.mass[action][source][target] = (
                        reserve * self.mass[action][source][target] + flow
                    ) / (reserve + one)
                    self.relation[action][source][target] = (
                        reserve * self.relation[action][source][target] + flow * x * y
                    ) / (reserve + flow)

        forecasts = []
        for action in range(actions):
            prediction = [half] * self.width
            for target in range(self.width):
                source = max(
                    range(self.width),
                    key=lambda index: self.mass[action][index][target]
                    * abs(self.relation[action][index][target]),
                )
                prediction[target] += (
                    half * self.relation[action][source][target]
                    * (two * obs[source] - one)
                )
            forecasts.append([min(one, max(False, value)) for value in prediction])

        self.edges = sum(
            max(self.mass[action][source][target]
                * abs(self.relation[action][source][target])
                for action in range(actions) for source in range(self.width))
            for target in range(self.width)
        )
        self.predictions = forecasts
        self.previous = list(obs)
        return forecasts[self.last_action or False]

    def act(self, obs):
        actions = len(self.mass)
        scores = []
        for action in range(actions):
            scores.append(sum(
                max(self.mass[action][source][target]
                    * abs(self.relation[action][source][target])
                    for source in range(self.width))
                for target in range(self.width)
            ))
        selected = max(range(actions), key=lambda action: scores[action])
        self.last_action = selected
        return selected

    def structure(self):
        mass = sum(sum(sum(row) for row in action) for action in self.mass or ())
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * len(self.mass or ()) * 16,
                "action_resource": mass}
