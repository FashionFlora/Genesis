"""Relations compete for a finite predictive metabolism."""

PARAMS = {"prior": 0.5, "unit": 1.0, "two": 2.0, "support": 3.0,
          "seed": 0.5, "decay": 0.98, "surprise": 0.1,
          "gain": 0.11, "floor": 0.025, "gate": 0.015}


class System:
    def __init__(self):
        self.width = False
        self.counts = None
        self.energy = None
        self.previous = None
        self.last_prediction = None
        self.mass = False

    def step(self, obs):
        if self.counts is None:
            self.width = len(obs)
            self.counts = [[[[False, False] for _ in (False, True)]
                            for _ in range(self.width)] for _ in range(self.width)]
            self.energy = [[PARAMS["seed"] for _ in range(self.width)]
                           for _ in range(self.width)]
        prediction = [PARAMS["prior"] for _ in obs]
        selected = [False for _ in obs]
        live = False
        for target in range(self.width):
            best = PARAMS["gate"]
            for source in range(self.width):
                zero, one = self.counts[source][target]
                p0 = (zero[1] + PARAMS["unit"]) / (zero[0] + PARAMS["two"])
                p1 = (one[1] + PARAMS["unit"]) / (one[0] + PARAMS["two"])
                support = zero[0] + one[0]
                score = abs(p1 - p0) * support / (support + PARAMS["support"])
                score *= self.energy[source][target]
                if score > best:
                    best = score
                    selected[target] = source
            source = selected[target]
            if best > PARAMS["gate"]:
                bit = int(obs[source])
                cell = self.counts[source][target][bit]
                prediction[target] = (cell[1] + PARAMS["unit"]) / (cell[0] + PARAMS["two"])
                live += int(source != target)
        if self.previous is not None:
            for source in range(self.width):
                bit = int(self.previous[source])
                for target in range(self.width):
                    error = abs(float(obs[target]) - self.last_prediction[target])
                    decay = PARAMS["decay"] - PARAMS["surprise"] * error
                    reward = PARAMS["prior"] - error * error
                    value = self.energy[source][target] * decay + PARAMS["gain"] * reward
                    self.energy[source][target] = max(False, min(PARAMS["unit"], value))
                    if self.energy[source][target] < PARAMS["floor"]:
                        self.counts[source][target] = [[False, False], [False, False]]
                    else:
                        cell = self.counts[source][target][bit]
                        cell[0] = cell[0] * decay + PARAMS["unit"]
                        cell[1] = cell[1] * decay + float(obs[target])
        self.mass = live
        self.previous = [int(value) for value in obs]
        self.last_prediction = prediction
        return prediction

    def structure(self):
        return {"units": self.mass, "connections": self.mass,
                "memory_bytes": self.width * self.width * 40}
