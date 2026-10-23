"""Retrieve local predictive states by their prequential fit."""

PARAMS = {"actions": 4}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.last_action = 0
        self.models = {}
        self.errors = {}
        self.prediction = []

    def _cell(self, action, source, target, state):
        key = (action, source, target, state)
        if key not in self.models:
            self.models[key] = [1.0, 1.0]
            self.errors[key] = 0.0
        return key, self.models[key]

    def step(self, obs):
        if self.previous is None:
            self.width = len(obs)
            self.previous = list(obs)
            self.prediction = [0.5] * self.width
            return self.prediction

        predictions = [0.5] * self.width
        selected = {}
        for target in range(self.width):
            candidates = []
            for source, active in enumerate(self.previous):
                if not active:
                    continue
                pair = []
                for state in range(2):
                    key, counts = self._cell(self.last_action, source, target, state)
                    probability = counts[1] / sum(counts)
                    pair.append((self.errors[key], probability, key, counts))
                chosen = min(pair, key=lambda item: item[0])
                candidates.append((abs(pair[0][1] - pair[1][1]), source, chosen))
            if candidates:
                _, source, chosen = max(candidates, key=lambda item: item[0])
                error, probability, key, counts = chosen
                predictions[target] = probability
                selected[target] = (key, counts, probability)

        for target, (key, counts, probability) in selected.items():
            value = float(obs[target])
            self.errors[key] += (value - probability) ** 2
            counts[int(value)] += 1.0

        self.previous = list(obs)
        self.prediction = predictions
        return predictions

    def act(self, obs):
        actions = int(PARAMS["actions"])
        scores = []
        for action in range(actions):
            uncertainty = 0.0
            for source, active in enumerate(obs):
                if active:
                    for target in range(len(obs)):
                        pair = [self._cell(action, source, target, state)[1]
                                for state in range(2)]
                        uncertainty += sum(1.0 / sum(cell) for cell in pair)
            scores.append(uncertainty)
        self.last_action = max(range(actions), key=scores.__getitem__)
        return self.last_action

    def structure(self):
        return {"units": self.width, "connections": len(self.models),
                "memory_bytes": len(self.models) * 32}
