"""Returned local transition flow used for prediction and action."""
PARAMS = {"timescale": 16.0, "decay": 0.97, "return": 0.8}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.edges = {}
        self.incoming = {}
        self.action_mass = [0.0] * 4
        self.last_action = 0
        self.last_target = None
        self.address = None

    def _flow(self, source, target, value):
        key = (source, target)
        old = self.edges.get(key, (0.0, 0.0))
        scale = PARAMS["timescale"]
        mean = (scale * old[0] + value) / (scale + 1.0)
        mass = old[1] + 1.0 / (1.0 + value * value)
        self.edges[key] = (mean, mass)
        self.incoming.setdefault(target, set()).add(source)

    def step(self, obs):
        if self.previous is None:
            self.width = len(obs)
            self.previous = list(obs)
            return [0.5] * self.width
        for source, before in enumerate(self.previous):
            x = 2.0 * before - 1.0
            for target, after in enumerate(obs):
                self._flow(source, target, x * (2.0 * after - 1.0))
        prediction = [0.5] * self.width
        for target, sources in self.incoming.items():
            if sources:
                source = max(sources, key=lambda index: abs(self.edges[index, target][0]) *
                             (1.0 + self.edges[index, target][1]))
                prediction[target] += 0.5 * self.edges[source, target][0] * (2.0 * self.previous[source] - 1.0)
        self.previous = list(obs)
        return [min(1.0, max(0.0, value)) for value in prediction]

    def act(self, obs):
        # The four action scores are returned transition flow from food to a
        # candidate head cell.  No score is tied to food consumption.
        active = [index for index, value in enumerate(obs) if value]
        if self.previous is None:
            self.previous = list(obs)
        heads = [index for index in active if index < 400]
        foods = [index for index in active if 500 <= index < 600]
        if heads and foods:
            head = heads[0]
            cell = head % 100
            x, y = cell % 10, cell // 10
            self.address = (x, y, foods[0] % 100)
            scores = []
            for action in range(4):
                dx, dy = ((0, -1), (1, 0), (0, 1), (-1, 0))[action]
                nx, ny = x + dx, y + dy
                target = 500 + (foods[0] % 100)
                candidate = action * 100 + ny * 10 + nx
                value = self.edges.get((target, candidate), (0.0, 0.0)) if 0 <= nx < 10 and 0 <= ny < 10 else (0.0, 0.0)
                scores.append(abs(value[0]) * (1.0 + value[1]))
            self.action_mass = [PARAMS["decay"] * mass + score
                                for mass, score in zip(self.action_mass, scores)]
        choice = max(range(4), key=lambda action: self.action_mass[action] +
                     PARAMS["return"] * float(action == self.last_action))
        self.last_action = choice
        return choice

    def structure(self):
        return {"units": self.width, "connections": len(self.edges),
                "memory_bytes": max(1, len(self.edges)) * 16,
                "action_resource": sum(self.action_mass)}
