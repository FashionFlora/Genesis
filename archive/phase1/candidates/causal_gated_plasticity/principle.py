"""Prediction error gates exploration; dormant causal models are conserved."""

PARAMS = {"error_gate": 0.18, "error_streak": 5}


class System:
    def __init__(self):
        self.n = 0
        self.previous = None
        self.models = []
        self.quality = []
        self.active = []
        self.errors = []
        self.cursor = []

    def _new(self):
        self.models = [[[[0.0, 0.0] for _ in range(2)] for _ in range(2)]
                       for _ in range(self.n) for _ in range(self.n)]
        self.quality = [[[0.0, 0.0] for _ in range(2)]
                        for _ in range(self.n) for _ in range(self.n)]
        self.active = [0 for _ in range(self.n)]
        self.errors = [0 for _ in range(self.n)]
        self.cursor = [0 for _ in range(self.n)]

    def _predict(self, target, source, rule, bit):
        cell = self.models[target * self.n + source][rule][bit]
        estimate = (cell[1] + 1.0) / (cell[0] + 2.0)
        return estimate if rule == 0 else 1.0 - estimate

    def step(self, obs):
        if not self.models:
            self.n = len(obs)
            self._new()
        if self.previous is not None:
            gate = PARAMS["error_gate"]
            limit = int(PARAMS["error_streak"])
            for target in range(self.n):
                index = self.active[target]
                source, rule = divmod(index, 2)
                bit = int(self.previous[source])
                prediction = self._predict(target, source, rule, bit)
                value = float(obs[target])
                loss = (prediction - value) ** 2
                cell = self.models[target * self.n + source][rule][bit]
                cell[0] += 1.0
                cell[1] += value if rule == 0 else 1.0 - value
                quality = self.quality[target * self.n + source][rule]
                quality[0] += 1.0
                quality[1] += float(loss <= gate)
                self.errors[target] = self.errors[target] + 1 if loss > gate else 0
                if self.errors[target] >= limit:
                    choices = []
                    total = self.n * 2
                    for offset in range(1, total + 1):
                        candidate = (self.cursor[target] + offset) % total
                        c_source, c_rule = divmod(candidate, 2)
                        score = self.quality[target * self.n + c_source][c_rule]
                        seen = score[0]
                        fit = score[1] / seen if seen else 0.5
                        choices.append((fit, -offset, candidate))
                    _, _, self.active[target] = max(choices)
                    self.cursor[target] = self.active[target]
                    self.errors[target] = 0
        prediction = [0.5] * self.n
        if self.previous is not None:
            for target in range(self.n):
                source, rule = divmod(self.active[target], 2)
                prediction[target] = self._predict(
                    target, source, rule, int(self.previous[source]))
        self.previous = list(obs)
        return prediction

    def structure(self):
        connections = sum(index // 2 < self.n // 2 <= target
                          for target, index in enumerate(self.active))
        return {"units": self.n, "connections": connections,
                "memory_bytes": self.n * self.n * 40}
