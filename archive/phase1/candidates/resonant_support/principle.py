"""Fast coactivity selects a relation; slow resonance preserves its forecast."""

PARAMS = {"fast_decay": 0.97, "slow_decay": 0.995, "memory_weight": 0.08}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.fast = None
        self.slow = None
        self.edges = 0

    def step(self, obs):
        if self.fast is None:
            self.width = len(obs)
            self.fast = [[[[0.0, 0.0] for _ in range(2)]
                          for _ in range(self.width)] for _ in range(self.width)]
            self.slow = [[[[0.0, 0.0] for _ in range(2)]
                          for _ in range(self.width)] for _ in range(self.width)]
        if self.previous is not None:
            for source in range(self.width):
                state = int(self.previous[source])
                for target in range(self.width):
                    fast = self.fast[source][target][state]
                    slow = self.slow[source][target][state]
                    fast[0] = fast[0] * PARAMS["fast_decay"] + 1.0
                    fast[1] = fast[1] * PARAMS["fast_decay"] + float(obs[target])
                    slow[0] = slow[0] * PARAMS["slow_decay"] + 1.0
                    slow[1] = slow[1] * PARAMS["slow_decay"] + float(obs[target])
        prediction = [0.5] * self.width
        self.edges = 0
        for target in range(self.width):
            def gap(source):
                cell = self.fast[source][target]
                return abs((cell[1][1] + 1.0) / (cell[1][0] + 2.0)
                           - (cell[0][1] + 1.0) / (cell[0][0] + 2.0))
            source = max(range(self.width), key=gap)
            self.edges += (target >= self.width // 2) * (source < self.width // 2)
            state = int(obs[source])
            fast = self.fast[source][target][state]
            slow = self.slow[source][target][state]
            recent = (fast[1] + 1.0) / (fast[0] + 2.0)
            remembered = (slow[1] + 1.0) / (slow[0] + 2.0)
            weight = min(1.0, max(0.0, PARAMS["memory_weight"]))
            prediction[target] = (1.0 - weight) * recent + weight * remembered
        self.previous = list(obs)
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * 32}
