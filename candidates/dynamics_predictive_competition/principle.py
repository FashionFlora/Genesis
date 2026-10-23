"""Predictive relations compete for a normalized share of each target."""

import math

PARAMS = {"rate": 1.0, "decay": 0.97, "weight_decay": 0.90}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.counts = None
        self.log_weights = None
        self.last_forecasts = None

    def step(self, obs):
        if self.counts is None:
            self.width = len(obs)
            self.counts = [[[[0.0, 0.0] for _ in range(2)]
                            for _ in range(self.width)] for _ in range(self.width)]
            self.log_weights = [[0.0 for _ in range(self.width)]
                                for _ in range(self.width)]
        if self.previous is not None:
            for source in range(self.width):
                bit = int(self.previous[source])
                for target in range(self.width):
                    if self.last_forecasts is not None:
                        error = self.last_forecasts[source][target] - float(obs[target])
                        self.log_weights[source][target] = (
                            PARAMS["weight_decay"] * self.log_weights[source][target]
                            - PARAMS["rate"] * error * error
                        )
                    cell = self.counts[source][target][bit]
                    cell[0] = PARAMS["decay"] * cell[0] + 1.0
                    cell[1] = PARAMS["decay"] * cell[1] + float(obs[target])

        prediction = []
        forecasts = [[0.5 for _ in range(self.width)] for _ in range(self.width)]
        for target in range(self.width):
            peak = max(self.log_weights[source][target] for source in range(self.width))
            weights = [math.exp(self.log_weights[source][target] - peak)
                       for source in range(self.width)]
            total = sum(weights)
            mixed = 0.0
            for source in range(self.width):
                cell = self.counts[source][target][int(obs[source])]
                forecast = (cell[1] + 1.0) / (cell[0] + 2.0)
                forecasts[source][target] = forecast
                mixed += weights[source] * forecast
            prediction.append(mixed / total)
        self.last_forecasts = forecasts
        self.previous = [float(value) for value in obs]
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.width * self.width,
                "memory_bytes": self.width * self.width * 5 * 8}
