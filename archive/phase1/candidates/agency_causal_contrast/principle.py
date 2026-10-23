"""One action-conditioned effect field predicts and ranks interventions."""

PARAMS = {"timescale": 12.0, "uncertainty": 0.02, "exploration": 1.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.mean = None
        self.variance = [0.0] * 4
        self.count = [0.0] * 4
        self.last_action = None
        self.prediction = None

    def step(self, obs):
        self.width = len(obs)
        values = [float(value) for value in obs]
        if self.previous is None:
            self.previous = values
            self.mean = [[0.0] * self.width for _ in range(4)]
            self.prediction = [0.5] * self.width
            return list(self.prediction)

        if self.last_action is not None:
            action = self.last_action
            delta = [value - old for value, old in zip(values, self.previous)]
            n = self.count[action] + 1.0
            old_mean = self.mean[action]
            error = sum((change - prior) ** 2 for change, prior in zip(delta, old_mean)) / max(1, self.width)
            rate = 1.0 / n
            self.mean[action] = [prior + rate * (change - prior)
                                 for prior, change in zip(old_mean, delta)]
            self.variance[action] += rate * (error - self.variance[action])
            self.count[action] = n
            self.last_action = None

        self.previous = values
        action = max(range(4), key=self._score)
        self.prediction = [min(1.0, max(0.0, value + effect))
                           for value, effect in zip(values, self.mean[action])]
        return list(self.prediction)

    def _contrast(self, action):
        others = [other for other in range(4) if other != action]
        contrast = sum(
            sum((x - y) ** 2 for x, y in zip(self.mean[action], self.mean[other]))
            / max(1, self.width)
            for other in others
        ) / len(others)
        confidence = self.count[action] / (self.count[action] + PARAMS["timescale"])
        return confidence * contrast / (1.0 + self.variance[action])

    def _score(self, action):
        return (self._contrast(action)
                + PARAMS["exploration"] / (self.count[action] + 1.0))

    def act(self, obs):
        action = max(range(4), key=self._score)
        self.last_action = action
        return action

    def structure(self):
        return {"units": self.width,
                "connections": sum(self.count),
                "memory_bytes": self.width * 4 * 8 + 96}
