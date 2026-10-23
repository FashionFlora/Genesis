"""One context-action transition field supplies prediction, memory, and act."""


PARAMS = {"timescale": 8.0, "contexts": 8, "actions": 4}


class System:
    def __init__(self):
        self.previous = None
        self.last_action = 0
        self.width = 0
        self.global_field = None
        self.local_field = None
        self.context = 0
        self.edges = 0.0

    @staticmethod
    def _probability(cell, state):
        return (cell[state][1] + 1.0) / (cell[state][0] + 2.0)

    def _cell(self, field, index):
        if index not in field:
            field[index] = [[0.0, 0.0], [0.0, 0.0]]
        return field[index]

    def step(self, obs):
        if self.global_field is None:
            self.width = len(obs)
            self.previous = list(obs)
            contexts = int(PARAMS["contexts"])
            self.global_field = {}
            self.local_field = {}
            return [0.5] * self.width

        self.context = int(sum(self.previous[self.width // 2:])) % int(PARAMS["contexts"])
        decay = PARAMS["timescale"] / (PARAMS["timescale"] + 1.0)
        for source, state in enumerate(self.previous):
            for target, value in enumerate(obs):
                index = source * self.width + target
                for field in (self.global_field, self.local_field):
                    key = index if field is self.global_field else (
                        self.context, self.last_action, index)
                    cell = self._cell(field, key)[int(state)]
                    cell[0] = decay * cell[0] + 1.0
                    cell[1] = decay * cell[1] + float(value)

        prediction = [0.5] * self.width
        self.edges = 0.0
        for target in range(self.width):
            candidates = []
            for source in range(self.width):
                index = source * self.width + target
                global_cell = self._cell(self.global_field, index)
                local_cell = self._cell(self.local_field,
                                        (self.context, self.last_action, index))
                contrast = abs(self._probability(global_cell, 1)
                               - self._probability(global_cell, 0))
                evidence = min(1.0, sum(row[0] for row in global_cell) / 4.0)
                candidates.append((contrast * evidence, source))
            _, source = max(candidates)
            index = source * self.width + target
            global_cell = self._cell(self.global_field, index)
            local_cell = self._cell(self.local_field,
                                    (self.context, self.last_action, index))
            state = int(self.previous[source])
            global_prediction = self._probability(global_cell, state)
            local_prediction = self._probability(local_cell, state)
            weight = local_cell[state][0] / (local_cell[state][0]
                                             + global_cell[state][0] + 1.0)
            prediction[target] = ((1.0 - weight) * global_prediction
                                  + weight * local_prediction)
            self.edges += (target >= self.width // 2) * (source < self.width // 2)

        self.previous = list(obs)
        return prediction

    def act(self, obs):
        context = int(sum(obs[self.width // 2:])) % int(PARAMS["contexts"])
        scores = []
        for action in range(int(PARAMS["actions"])):
            uncertainty = 0.0
            for source, state in enumerate(obs):
                for target in range(len(obs)):
                    index = source * self.width + target
                    cell = self._cell(self.local_field, (context, action, index))
                    uncertainty += 1.0 / (sum(cell[0]) + sum(cell[1]) + 1.0)
            scores.append(uncertainty)
        self.last_action = max(range(len(scores)), key=scores.__getitem__)
        return self.last_action

    def structure(self):
        contexts = int(PARAMS["contexts"])
        actions = int(PARAMS["actions"])
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (1 + contexts * actions) * 32}
