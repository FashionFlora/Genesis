"""Contextual prediction survives when a dormant causal model fits better."""

PARAMS = {"timescale": 16.0, "contexts": 2, "actions": 4}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.active = None
        self.dormant = None
        self.prediction = None
        self.context = 0
        self.last_action = None
        self.action_outcomes = None
        self.edges = 0.0

    def _blank(self):
        return [[[[[0.0, 0.0] for _ in range(2)] for _ in range(self.width)]
                 for _ in range(self.width)]
                for _ in range(int(PARAMS["contexts"]))]

    def _probability(self, model, context, source, target, bit):
        cell = model[context][source][target][bit]
        return (cell[1] + 1.0) / (cell[0] + 2.0)

    def step(self, obs):
        if self.previous is None:
            self.width = len(obs)
            self.active = self._blank()
            self.dormant = self._blank()
            self.action_outcomes = [[0.0, 0.0] for _ in range(int(PARAMS["actions"]))]
            self.prediction = [0.5] * self.width
            self.previous = list(obs)
            return self.prediction

        self.context = int(sum(self.previous)) % int(PARAMS["contexts"])
        decay = PARAMS["timescale"] / (PARAMS["timescale"] + 1.0)
        if self.last_action is not None:
            cell = self.action_outcomes[self.last_action]
            change = sum(a != b for a, b in zip(self.previous, obs)) / self.width
            cell[0] = decay * cell[0] + 1.0
            cell[1] = decay * cell[1] + change

        for source, before in enumerate(self.previous):
            bit = int(before)
            for target, value in enumerate(obs):
                cell = self.active[self.context][source][target][bit]
                cell[0] = decay * cell[0] + 1.0
                cell[1] = decay * cell[1] + float(value)

        prediction = [0.5] * self.width
        self.edges = 0.0
        for target in range(self.width):
            source = max(range(self.width), key=lambda s: abs(
                self._probability(self.active, self.context, s, target, 1)
                - self._probability(self.active, self.context, s, target, 0)))
            bit = int(obs[source])
            active_p = self._probability(self.active, self.context, source, target, bit)
            dormant_p = self._probability(self.dormant, self.context, source, target, bit)
            active_error = (active_p - obs[target]) ** 2
            dormant_error = (dormant_p - obs[target]) ** 2
            if dormant_error < active_error:
                self.active[self.context][source][target], self.dormant[self.context][source][target] = (
                    self.dormant[self.context][source][target],
                    self.active[self.context][source][target])
                active_p = dormant_p
            prediction[target] = active_p
            self.edges += (target >= self.width // 2) * (source < self.width // 2)

        self.previous = list(obs)
        self.prediction = prediction
        return prediction

    def act(self, obs):
        uncertainty = []
        for total, changed in self.action_outcomes:
            probability = (changed + 0.5) / (total + 1.0)
            uncertainty.append(probability * (1.0 - probability))
        self.last_action = max(range(len(uncertainty)), key=uncertainty.__getitem__)
        return self.last_action

    def structure(self):
        contexts = int(PARAMS["contexts"])
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * contexts * 4 * 16}
