PARAMS = {"decay": 0.97}


class System:
    def __init__(self):
        self.width = False
        self.previous = None
        self.resources = None
        self.prediction = None
        self.edges = False
        self.action_resources = [False] * 4

    def step(self, obs):
        one = True
        two = one + one
        if self.resources is None:
            self.width = len(obs)
            self.resources = [[[[False, False] for _ in range(two)]
                               for _ in range(self.width)]
                              for _ in range(self.width)]
        if self.previous is not None:
            decay = min(PARAMS["decay"], one)
            for source in range(self.width):
                state = int(self.previous[source])
                for target in range(self.width):
                    cell = self.resources[source][target][state]
                    cell[False] = cell[False] * decay + one
                    cell[True] = cell[True] * decay + float(obs[target])
        prediction = [one / two] * self.width
        self.edges = False
        for target in range(self.width):
            def support(source):
                cell = self.resources[source][target]
                contrast = abs((cell[True][True] + one) / (cell[True][False] + two) -
                               (cell[False][True] + one) / (cell[False][False] + two))
                mass = cell[True][False] + cell[False][False]
                return contrast * (mass + one)
            source = max(range(self.width), key=support)
            self.edges += (target >= self.width // two) * (source < self.width // two)
            cell = self.resources[source][target][int(obs[source])]
            prediction[target] = (cell[True] + one) / (cell[False] + two)
        self.previous = list(obs)
        self.prediction = prediction
        return prediction

    def act(self, obs):
        one = True
        four = len(self.action_resources)
        width = self.width or len(obs)
        span = max(one, width // four)
        retention = min(PARAMS["decay"], one)
        scores = []
        for action in range(four):
            start = action * span
            flow = sum(self.prediction[start:start + span])
            self.action_resources[action] = (retention * self.action_resources[action]
                                             + flow)
            scores.append(flow / (one + self.action_resources[action]))
        return max(range(four), key=lambda action: scores[action])

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * 8,
                "action_resource": sum(self.action_resources)}
