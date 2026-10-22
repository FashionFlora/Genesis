"""Local predictive homeostasis: evidence, not reward, keeps a contact alive."""

PARAMS = {"fast_decay": 0.97, "slow_decay": 0.998, "slow_weight": 0.1}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.fast = []
        self.slow = []

    def step(self, observation):
        if self.previous is None:
            self.width = len(observation)
            self.fast = [[[[1.0, 1.0] for _ in range(2)]
                          for _ in range(self.width)] for _ in range(self.width)]
            self.slow = [[[[1.0, 1.0] for _ in range(2)]
                          for _ in range(self.width)] for _ in range(self.width)]
        else:
            for source in range(self.width):
                state = int(self.previous[source])
                for target in range(self.width):
                    fast = self.fast[source][target][state]
                    slow = self.slow[source][target][state]
                    fast[0] = PARAMS["fast_decay"] * fast[0] + 1.0
                    fast[1] = PARAMS["fast_decay"] * fast[1] + float(observation[target])
                    slow[0] = PARAMS["slow_decay"] * slow[0] + 1.0
                    slow[1] = PARAMS["slow_decay"] * slow[1] + float(observation[target])
        prediction = []
        for target in range(self.width):
            source = max(range(self.width), key=lambda index: self._gap(index, target))
            state = int(observation[source])
            fast = self.fast[source][target][state]
            slow = self.slow[source][target][state]
            recent = (fast[1] + 1.0) / (fast[0] + 2.0)
            remembered = (slow[1] + 1.0) / (slow[0] + 2.0)
            prediction.append((1.0 - PARAMS["slow_weight"]) * recent
                              + PARAMS["slow_weight"] * remembered)
        self.previous = list(observation)
        return prediction

    def _gap(self, source, target):
        cell = self.fast[source][target]
        one = (cell[1][1] + 1.0) / (cell[0][1] + 2.0)
        zero = (cell[1][0] + 1.0) / (cell[0][0] + 2.0)
        return abs(one - zero)

    def structure(self):
        support = sum(self._gap(source, target)
                      for target in range(self.width)
                      for source in range(self.width))
        return {"units": self.width + support, "connections": support,
                "memory_bytes": self.width * self.width * 64}
