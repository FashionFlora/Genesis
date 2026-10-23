"""Retain actions whose own sensory returns are repeatable in context."""

PARAMS = {"memory": 8.0}


class System:
    def __init__(self):
        self.width = 0
        self.last = None
        self.counts = [[0.0] * 4 for _ in range(2)]
        self.means = [[[] for _ in range(4)] for _ in range(2)]
        self.energy = [[0.0] * 4 for _ in range(2)]

    def step(self, obs):
        self.width = len(obs)
        if self.last is not None:
            action, context, before = self.last
            delta = [value - old for value, old in zip(obs, before)]
            count = self.counts[context][action] + 1.0
            rate = 1.0 / count
            mean = self.means[context][action] or [0.0] * self.width
            self.means[context][action] = [old + rate * (change - old)
                                           for old, change in zip(mean, delta)]
            energy = sum(change * change for change in delta)
            self.energy[context][action] += rate * (energy - self.energy[context][action])
            self.counts[context][action] = count
        self.last = None
        return [0.5] * self.width

    def _layout(self, obs):
        cells = len(obs) // 7
        side = int(cells ** 0.5)
        maps = [obs[i * cells:(i + 1) * cells] for i in range(7)]
        direction = next((d for d in range(4) if any(maps[d])), 0)
        head = next((i for i, value in enumerate(maps[direction]) if value), 0)
        return side, direction, head, maps[4]

    def act(self, obs):
        side, direction, head, body = self._layout(obs)
        x, y = head % side, head // side
        moves = ((0, -1), (1, 0), (0, 1), (-1, 0))
        legal = []
        for action, (dx, dy) in enumerate(moves):
            nx, ny = x + dx, y + dy
            if action == (direction + 2) % 4 or not (0 <= nx < side and 0 <= ny < side):
                continue
            if body[ny * side + nx]:
                continue
            legal.append(action)
        # The context is the number of continuations the intervention leaves.
        # It is observable from the same local state and does not name food.
        context = min(3, len(legal))
        if not legal:
            self.last = (direction, context, list(obs))
            return direction
        scores = []
        for action in legal:
            mean = self.means[context][action]
            predictable = sum(value * value for value in mean)
            noise = max(self.energy[context][action], 1.0 / PARAMS["memory"]) ** 0.5
            scores.append(predictable / noise + 1.0 / (1.0 + self.counts[context][action]))
        choice = legal[max(range(len(legal)), key=scores.__getitem__)]
        self.last = (choice, context, list(obs))
        return choice

    def structure(self):
        return {"units": self.width, "connections": sum(sum(row) for row in self.counts),
                "memory_bytes": 64 * sum(bool(mean) for row in self.means for mean in row)}
