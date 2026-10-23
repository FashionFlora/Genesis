"""Keep outcome predictors distinct by the context and action that caused them."""

from collections import defaultdict

PARAMS = {"actions": 4}


class System:
    def __init__(self):
        self.previous = None
        self.last_action = 0
        self.width = 0
        self.counts = defaultdict(lambda: [0.5, 0.5, 0.0])
        self.prediction = []

    def _cell(self, action, source, target, bit):
        return self.counts[action, source, target, bit]

    @staticmethod
    def _active_sources(obs):
        return [source for source, bit in enumerate(obs) if bit]

    def step(self, obs):
        if self.previous is None:
            self.width = len(obs)
            self.previous = list(obs)
            self.prediction = [0.5] * self.width
            return self.prediction

        for source in self._active_sources(self.previous):
            cell_bit = 1
            for target, value in enumerate(obs):
                cell = self._cell(self.last_action, source, target, cell_bit)
                cell[0] += float(value)
                cell[1] += 1.0 - float(value)
                cell[2] += 1.0

        prediction = [0.5] * self.width
        edges = 0
        for target in range(self.width):
            candidates = []
            for source in self._active_sources(self.previous):
                zero = self._cell(self.last_action, source, target, 0)
                one = self._cell(self.last_action, source, target, 1)
                p_zero = zero[0] / (zero[0] + zero[1])
                p_one = one[0] / (one[0] + one[1])
                candidates.append((abs(p_one - p_zero), source, p_zero, p_one))
            if candidates:
                contrast, source, p_zero, p_one = max(candidates)
                edges += int(contrast > 0.0)
                prediction[target] = p_one

        self.previous = list(obs)
        self.prediction = prediction
        return prediction

    def act(self, obs):
        width = len(obs)
        scores = []
        for action in range(int(PARAMS["actions"])):
            uncertainty = 0.0
            for source in self._active_sources(obs):
                for target in range(width):
                    cell = self._cell(action, source, target, 1)
                    uncertainty += 1.0 / (cell[2] + 1.0)
            scores.append(uncertainty)
        self.last_action = max(range(len(scores)), key=scores.__getitem__)
        return self.last_action

    def structure(self):
        return {"units": self.width, "connections": sum(
            int(cell[2] > 0.0) for cell in self.counts.values()),
            "memory_bytes": len(self.counts) * 24}
