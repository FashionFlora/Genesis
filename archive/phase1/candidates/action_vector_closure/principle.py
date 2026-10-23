"""A compact action-conditioned transition law predicts and selects."""

PARAMS = {"timescale": 16.0, "variance": 0.01, "exploration": 1.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.mean = None
        self.var = None
        self.count = [0.0] * 4
        self.last_action = None
        self.predicted = None
        self.connections = 0.0

    def _observe_effect(self, obs):
        if self.previous is None:
            self.width = len(obs)
            self.previous = list(obs)
            self.mean = [[0.0] * self.width for _ in range(4)]
            self.var = [0.0] * 4
            return
        if self.last_action is not None:
            action = self.last_action
            delta = [float(value) - float(before)
                     for value, before in zip(obs, self.previous)]
            rate = 1.0 / (self.count[action] + 1.0)
            error = sum((value - old) ** 2
                        for value, old in zip(delta, self.mean[action])) / self.width
            self.mean[action] = [old + rate * (value - old)
                                 for value, old in zip(delta, self.mean[action])]
            self.var[action] += rate * (error - self.var[action])
            self.count[action] += 1.0
            self.last_action = None
        self.previous = list(obs)

    def step(self, obs):
        predicted = self.predicted
        self._observe_effect(obs)
        self.predicted = None
        return [0.5] * len(obs) if predicted is None else predicted

    def act(self, obs):
        self._observe_effect(obs)

        def score(action):
            signal = sum(value * value for value in self.mean[action]) / max(1, self.width)
            return (signal / (self.var[action] + PARAMS["variance"])
                    + PARAMS["exploration"] / (self.count[action] + 1.0))

        action = max(range(4), key=score)
        self.last_action = action
        self.predicted = [min(1.0, max(0.0, float(value) + effect))
                          for value, effect in zip(obs, self.mean[action])]
        return action

    def structure(self):
        return {"units": self.width, "connections": self.connections + sum(self.count),
                "memory_bytes": self.width * 4 * 8 + 64}
