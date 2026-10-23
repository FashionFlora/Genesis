"""Predictive distinctions persist only when they explain the next transition."""

PARAMS = {"decay": 0.96, "slots": 4, "persistence": 4}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.models = []
        self.active = 0
        self.usage = []
        self.challenger = None
        self.streak = 0
        self.edges = 0

    def _blank(self):
        return [[[[1.0, 1.0], [1.0, 1.0]] for _ in range(self.width)]
                for _ in range(self.width)]

    @staticmethod
    def _prob(cell, state):
        return (cell[state][1] + 1.0) / (cell[state][0] + 2.0)

    def _source(self, model, target):
        return max(
            range(self.width),
            key=lambda source: abs(
                self._prob(model[source][target], 1)
                - self._prob(model[source][target], 0)))

    def _predict(self, model, previous):
        output = [0.5] * self.width
        for target in range(self.width):
            source = self._source(model, target)
            output[target] = self._prob(model[source][target], int(previous[source]))
        return output

    def _error(self, model, previous, observation):
        prediction = self._predict(model, previous)
        return sum((guess - value) ** 2
                   for guess, value in zip(prediction, observation)) / self.width

    def _update(self, model, previous, observation):
        decay = min(1.0, PARAMS["decay"])
        for source, before in enumerate(previous):
            state = int(before)
            for target, value in enumerate(observation):
                cell = model[source][target][state]
                cell[0] = decay * cell[0] + 1.0
                cell[1] = decay * cell[1] + float(value)

    def step(self, observation):
        if not self.models:
            self.width = len(observation)
            self.models = [[self._blank() for _ in range(int(PARAMS["slots"]))]][0]
            self.usage = [0] * len(self.models)
            self.previous = list(observation)
            return [0.5] * self.width

        if self.previous is not None:
            errors = [self._error(model, self.previous, observation)
                      for model in self.models]
            best = min(range(len(self.models)), key=errors.__getitem__)
            if best != self.active and errors[best] < errors[self.active]:
                self.streak = self.streak + 1 if self.challenger == best else 1
                self.challenger = best
                if self.streak >= int(PARAMS["persistence"]):
                    self.active = best
                    self.challenger = None
                    self.streak = 0
            else:
                self.challenger = None
                self.streak = 0
            self._update(self.models[self.active], self.previous, observation)
            self.usage[self.active] += 1

        prediction = self._predict(self.models[self.active], observation)
        self.edges = 0
        for target in range(self.width):
            source = self._source(self.models[self.active], target)
            self.edges += source < self.width // 2 <= target
        self.previous = list(observation)
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": len(self.models) * self.width * self.width * 16}
