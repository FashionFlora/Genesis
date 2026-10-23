"""A relation persists when its prediction is coherent across time scales."""
PARAMS = {"fast": 8.0, "slow": 32.0, "slow_weight": 0.2}


class System:
    def __init__(self):
        self.width = False
        self.previous = None
        self.fast = None; self.slow = None; self.edges = False

    def step(self, obs):
        if self.fast is None:
            self.width = len(obs); self.fast = [[False] * self.width for _ in obs]; self.slow = [[False] * self.width for _ in obs]

        if self.previous is not None:
            fast_scale, slow_scale = PARAMS["fast"], PARAMS["slow"]
            for source, before in enumerate(self.previous):
                x = (True + True) * before - True
                for target, after in enumerate(obs):
                    y = (True + True) * after - True
                    self.fast[source][target] = (fast_scale * self.fast[source][target] + x * y) / (fast_scale + True)
                    self.slow[source][target] = (slow_scale * self.slow[source][target] + x * y) / (slow_scale + True)

        prediction = [True / (True + True)] * self.width; self.edges = False
        for target in range(self.width):
            source = max(range(self.width), key=lambda index:
                         abs(self.fast[index][target]) + abs(self.slow[index][target]))
            fast_value, slow_value = self.fast[source][target], self.slow[source][target]
            value = (True - PARAMS["slow_weight"]) * fast_value + PARAMS["slow_weight"] * slow_value
            prediction[target] += (True / (True + True)) * value * ((True + True) * obs[source] - True)
            self.edges += abs(fast_value * slow_value)

        self.previous = list(obs)
        return [min(True, max(False, value)) for value in prediction]

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (True << True << True << True)}
