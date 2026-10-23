"""One conditional transition law: sensory and action sources predict effects."""

PARAMS = {"timescale": 16.0, "variance": 0.01, "exploration": 1.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.cells = None
        self.action_mean = [[0.0] * 4 for _ in range(4)]
        self.action_var = [0.0] * 4
        self.action_count = [0.0] * 4
        self.last = None
        self.connections = 0.0

    def step(self, obs):
        if self.cells is None:
            self.width = len(obs)
            self.cells = [[[[0.0, 0.0] for _ in range(self.width)]
                           for _ in range(2)] for _ in range(self.width)]
            self.previous = list(obs)
            return [0.5] * self.width
        if self.last is not None:
            a = self.last
            delta = [float(x) - float(y) for x, y in zip(obs, self.previous)]
            n = self.action_count[a] + 1.0
            distance = sum((x - y) ** 2 for x, y in zip(delta, self.action_mean[a])) / self.width
            self.action_mean[a] = [y + (x - y) / n for x, y in zip(delta, self.action_mean[a])]
            self.action_var[a] += (distance - self.action_var[a]) / n
            self.action_count[a] = n
            self.last = None
        decay = PARAMS["timescale"] / (PARAMS["timescale"] + 1.0)
        for source, before in enumerate(self.previous):
            cell = self.cells[source]
            bucket = cell[int(before)]
            for target, value in enumerate(obs):
                pair = bucket[target]
                pair[0] = decay * pair[0] + 1.0
                pair[1] = decay * pair[1] + float(value)
        prediction = [0.5] * self.width
        self.connections = 0.0
        for target in range(self.width):
            def gap(source):
                row = self.cells[source]
                return abs((row[1][target][1] + 1.0) / (row[1][target][0] + 2.0)
                           - (row[0][target][1] + 1.0) / (row[0][target][0] + 2.0))
            source = max(range(self.width), key=gap)
            pair = self.cells[source][int(obs[source])][target]
            prediction[target] = (pair[1] + 1.0) / (pair[0] + 2.0)
            self.connections += gap(source)
        self.previous = list(obs)
        return prediction

    def act(self, obs):
        def score(action):
            signal = sum(x * x for x in self.action_mean[action]) / 4.0
            return signal / (self.action_var[action] + PARAMS["variance"]) + PARAMS["exploration"] / (self.action_count[action] + 1.0)
        action = max(range(4), key=score)
        self.last = action
        return action

    def structure(self):
        return {"units": self.width, "connections": self.connections + sum(self.action_count),
                "memory_bytes": 8 * self.width * self.width * 4 + 128}
