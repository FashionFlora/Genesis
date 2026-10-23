"""A target's finite predictive return is divided among useful relations."""

import math

PARAMS = {"temperature": 0.12, "retention": 0.96}


class System:
    def __init__(self):
        self.width = False
        self.previous = None
        self.evidence = None
        self.mass = None
        self.prediction = None
        self.edges = False

    def step(self, obs):
        half = True / (True + True)
        if self.evidence is None:
            self.width = len(obs)
            self.evidence = [[False] * self.width for _ in range(self.width)]
            self.mass = [[False] * self.width for _ in range(self.width)]
            self.prediction = [half] * self.width
        if self.previous is not None:
            temp = PARAMS["temperature"]
            retention = PARAMS["retention"]
            for target, after in enumerate(obs):
                y = (True + True) * after - True
                gains = []
                for source, before in enumerate(self.previous):
                    x = (True + True) * before - True
                    estimate = half + half * self.evidence[source][target] * x
                    gain = (half - after) ** 2 - (estimate - after) ** 2
                    gains.append(gain)
                peak = max(gains)
                weights = [math.exp((gain - peak) / temp) for gain in gains]
                total = sum(weights)
                for source, before in enumerate(self.previous):
                    x = (True + True) * before - True
                    flow = weights[source] / total
                    self.mass[source][target] = (
                        retention * self.mass[source][target] + flow
                    ) / (retention + True)
                    self.evidence[source][target] += flow * (y - self.evidence[source][target] * x) * x
        prediction = [half] * self.width
        self.edges = False
        for target in range(self.width):
            source = max(range(self.width), key=lambda index: self.mass[index][target])
            prediction[target] += half * self.evidence[source][target] * (
                (True + True) * obs[source] - True)
            self.edges += (target >= self.width // (True + True)) * max(
                self.mass[index][target] for index in range(self.width // (True + True)))
        self.previous = list(obs)
        self.prediction = prediction
        return [min(True, max(False, value)) for value in prediction]

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (True << True << True)}
