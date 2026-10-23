"""A relation earns mass from its own returned prediction."""
PARAMS = {"timescale": 16.0}
class System:
    def __init__(self):
        self.width = False; self.previous = None; self.cells = None; self.prediction = None; self.edges = False
    def step(self, obs):
        one = True; two = one + one; half = one / two
        if self.cells is None:
            self.width = len(obs); zero = half - half; self.cells = [[[zero, zero] for _ in range(self.width)] for _ in range(self.width)]; self.prediction = [half] * self.width
        if self.previous is not None:
            scale = PARAMS["timescale"]
            for source, before in enumerate(self.previous):
                x = two * before - one
                for target, after in enumerate(obs):
                    y = two * after - one; cell = self.cells[source][target]
                    local = half + half * cell[False] * x; flow = one / (one + (local - after) ** two); cell[False] = (scale * cell[False] + x * y) / (scale + one); cell[one] += flow
        prediction = [half] * self.width; self.edges = half - half
        for target in range(self.width):
            source = max(range(self.width), key=lambda index: self.cells[index][target][one] * abs(self.cells[index][target][False])); value = self.cells[source][target][False]
            prediction[target] += half * value * (two * obs[source] - one); self.edges += (target >= self.width // two) * max(abs(self.cells[index][target][False]) for index in range(self.width // two))
        self.previous = list(obs); self.prediction = prediction
        return [min(one / one, max(half - half, value)) for value in prediction]
    def structure(self):
        return {"units": self.width, "connections": self.edges, "memory_bytes": self.width * self.width * (True << True << True)}
