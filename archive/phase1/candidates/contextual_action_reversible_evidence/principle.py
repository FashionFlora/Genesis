"""Context-indexed action predictors preserve evidence across recurrence."""

from collections import defaultdict

PARAMS = {"actions": 4, "contexts": 2}


class System:
    def __init__(self):
        self.previous = None
        self.last_action = 0
        self.width = 0
        self.cells = defaultdict(lambda: [0.5, 0.5])
        self.prediction = []
        self.context = 0

    def _key(self, context, action, source, target, bit):
        return context, action, source, target, bit

    def step(self, obs):
        if self.previous is None:
            self.width = len(obs)
            self.previous = list(obs)
            self.prediction = [0.5] * self.width
            return self.prediction

        self.context = int(sum(self.previous)) % int(PARAMS["contexts"])
        for source, before in enumerate(self.previous):
            for target, value in enumerate(obs):
                cell = self.cells[self._key(self.context, self.last_action, source,
                                            target, int(before))]
                cell[0] += float(value)
                cell[1] += 1.0 - float(value)

        prediction = [0.5] * self.width
        for target in range(self.width):
            sources = [source for source, bit in enumerate(self.previous) if bit]
            if sources:
                source = max(sources, key=lambda item: self.cells[
                    self._key(self.context, self.last_action, item, target, 1)][0]
                    + self.cells[self._key(self.context, self.last_action,
                                           item, target, 1)][1])
                cell = self.cells[self._key(self.context, self.last_action,
                                            source, target, 1)]
                prediction[target] = cell[0] / sum(cell)
        self.previous = list(obs)
        self.prediction = prediction
        return prediction

    def act(self, obs):
        context = int(sum(obs)) % int(PARAMS["contexts"])
        width = len(obs)
        scores = []
        for action in range(int(PARAMS["actions"])):
            uncertainty = 0.0
            for source, bit in enumerate(obs):
                for target in range(width):
                    cell = self.cells[self._key(context, action, source,
                                                target, int(bit))]
                    uncertainty += 1.0 / sum(cell)
            scores.append(uncertainty)
        self.last_action = max(range(len(scores)), key=scores.__getitem__)
        return self.last_action

    def structure(self):
        return {"units": self.width,
                "connections": sum(1 for cell in self.cells.values()
                                    if sum(cell) > 1.0),
                "memory_bytes": len(self.cells) * 16}
