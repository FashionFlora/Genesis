"""Context-indexed causal support; act samples the least certain intervention."""

PARAMS = {"timescale": 16.0, "contexts": 2, "actions": 4, "context_weight": 0.10}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.support = None
        self.context_support = None
        self.prediction = None
        self.context = 0
        self.edges = 0.0
        self.action_total = [0.0] * int(PARAMS["actions"])
        self.action_change = [0.0] * int(PARAMS["actions"])
        self.last_action = None

    def step(self, obs):
        one = 1.0
        if self.support is None:
            self.width = len(obs)
            self.support = [[0.0] * self.width for _ in range(self.width)]
            self.context_support = [[[0.0] * self.width for _ in range(self.width)]
                                    for _ in range(int(PARAMS["contexts"]))]
            self.prediction = [0.5] * self.width
        if self.previous is not None:
            scale = PARAMS["timescale"]
            self.context = int(sum(self.previous)) % int(PARAMS["contexts"])
            if self.last_action is not None:
                change = sum(before != after for before, after in zip(self.previous, obs)) / self.width
                action = self.last_action
                self.action_total[action] += one
                self.action_change[action] = (scale * self.action_change[action] + change) / (scale + one)
            for source, before in enumerate(self.previous):
                x = 2.0 * before - one
                for target, after in enumerate(obs):
                    y = 2.0 * after - one
                    self.support[source][target] = (scale * self.support[source][target] + x * y) / (scale + one)
                    local = self.context_support[self.context][source]
                    local[target] = (scale * local[target] + x * y) / (scale + one)
        prediction = [0.5] * self.width
        self.edges = 0.0
        weight = PARAMS["context_weight"]
        for target in range(self.width):
            source = max(range(self.width), key=lambda index: abs(self.support[index][target]))
            value = self.support[source][target]
            local = self.context_support[self.context][source][target]
            value += weight * (one - min(one, abs(value))) * local
            prediction[target] += 0.5 * value * (2.0 * obs[source] - one)
            self.edges += (target >= self.width // 2) * max(
                abs(self.support[index][target]) for index in range(self.width // 2))
        self.previous = list(obs)
        self.prediction = prediction
        return [min(one, max(0.0, value)) for value in prediction]

    def act(self, obs):
        """Choose the intervention whose observed outcome remains most uncertain."""
        scores = []
        for total, changed in zip(self.action_total, self.action_change):
            probability = (changed + 0.5) / (total + 1.0)
            scores.append(probability * (1.0 - probability))
        self.last_action = max(range(len(scores)), key=scores.__getitem__)
        return self.last_action

    def structure(self):
        contexts = int(PARAMS["contexts"])
        actions = int(PARAMS["actions"])
        return {"units": self.width,
                "connections": self.edges,
                "memory_bytes": self.width * self.width * (contexts + 1) * 8 + actions * 16}
