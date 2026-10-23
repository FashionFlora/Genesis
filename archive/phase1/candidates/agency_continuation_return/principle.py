"""Actions persist when their observed consequence preserves future control."""

PARAMS = {"exploration": 1.0, "timescale": 16.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.prediction = None
        self.last = None
        self.count = [0.0] * 4
        self.returned = [0.0] * 4
        self.mobility = 0.0
        self.support = None
        self.mass = None
        self.edges = 0.0

    def _layout(self, obs):
        cells = len(obs) // 7
        side = int(cells ** 0.5)
        direction = next((a for a in range(4)
                          if any(obs[a * cells:(a + 1) * cells])), 0)
        head = next((i for i, value in enumerate(
            obs[direction * cells:(direction + 1) * cells]) if value), 0)
        return side, direction, head, obs[4 * cells:5 * cells]

    def _mobility(self, side, direction, head, body):
        x, y = head % side, head // side
        moves = ((0, -1), (1, 0), (0, 1), (-1, 0))
        return sum(0 <= x + dx < side and 0 <= y + dy < side
                   and a != (direction + 2) % 4
                   and not body[(y + dy) * side + x + dx]
                   for a, (dx, dy) in enumerate(moves))

    def step(self, obs):
        self.width = len(obs)
        side, direction, head, body = self._layout(obs)
        now = self._mobility(side, direction, head, body)
        if self.last is not None:
            action, before = self.last
            n = self.count[action] + 1.0
            self.returned[action] += (now - self.returned[action]) / n
            self.count[action] = n
            self.last = None
        if self.previous is None:
            self.previous = list(obs)
            self.prediction = [0.5] * self.width
            return list(self.prediction)
        if self.support is None and self.width <= 64:
            self.support = [[0.0] * self.width for _ in range(self.width)]
            self.mass = [[1.0 / self.width] * self.width for _ in range(self.width)]
        if self.support is not None:
            for target, after in enumerate(obs):
                flows = []
                for source, before in enumerate(self.previous):
                    x, y = 2.0 * before - 1.0, 2.0 * after - 1.0
                    old = self.support[source][target]
                    error = (0.5 + 0.5 * old * x - after) ** 2
                    flow = self.mass[source][target] / (1.0 + error)
                    flows.append(flow)
                    scale = PARAMS["timescale"]
                    self.support[source][target] = (scale * old + flow * x * y) / (scale + flow)
                total = sum(flows)
                if total:
                    for source, flow in enumerate(flows):
                        self.mass[source][target] = flow / total
            prediction = [0.5] * self.width
            self.edges = 0.0
            for target in range(self.width):
                for source in range(self.width):
                    value = self.mass[source][target] * self.support[source][target]
                    prediction[target] += 0.5 * value * (2.0 * obs[source] - 1.0)
                    self.edges += abs(value)
            self.prediction = [min(1.0, max(0.0, value)) for value in prediction]
        self.previous = list(obs)
        self.mobility = now
        return list(self.prediction or [0.5] * self.width)

    def act(self, obs):
        side, direction, head, body = self._layout(obs)
        x, y = head % side, head // side
        moves = ((0, -1), (1, 0), (0, 1), (-1, 0))
        legal = [a for a, (dx, dy) in enumerate(moves)
                 if a != (direction + 2) % 4 and 0 <= x + dx < side
                 and 0 <= y + dy < side and not body[(y + dy) * side + x + dx]]
        if not legal:
            return direction
        scores = [self.returned[a] + PARAMS["exploration"] / (self.count[a] + 1.0)
                  for a in legal]
        choice = legal[max(range(len(legal)), key=scores.__getitem__)]
        self.last = (choice, self.mobility)
        return choice

    def structure(self):
        return {"units": self.width + self.mobility, "connections": self.edges + sum(self.count),
                "memory_bytes": 8 * len(self.count) +
                16 * self.width * self.width if self.support is not None else 8 * len(self.count)}
