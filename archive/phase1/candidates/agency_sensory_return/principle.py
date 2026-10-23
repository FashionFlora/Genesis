"""Order legal actions by the predictable part of their sensory return."""

PARAMS = {"memory": 8.0}


class System:
    def __init__(self):
        self.last = None
        self.width = 0
        self.counts = [0.0] * 4
        self.means = [[] for _ in range(4)]
        self.energy = [0.0] * 4

    def step(self, obs):
        self.width = len(obs)
        if self.last is not None:
            action, before = self.last
            delta = [value - old for value, old in zip(obs, before)]
            count = self.counts[action] + 1.0
            rate = 1.0 / count
            if not self.means[action]:
                self.means[action] = [0.0] * self.width
            self.means[action] = [mean + rate * (change - mean)
                                  for mean, change in zip(self.means[action], delta)]
            self.energy[action] += rate * (sum(change * change for change in delta)
                                           - self.energy[action])
            self.counts[action] = count
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
        if not legal:
            self.last = (direction, list(obs))
            return direction
        scores = []
        for action in legal:
            mean = self.means[action]
            predictable = sum(value * value for value in mean)
            scores.append(predictable / max(self.energy[action], 1.0 / PARAMS["memory"]) ** 0.5)
        choice = legal[max(range(len(legal)), key=scores.__getitem__)]
        self.last = (choice, list(obs))
        return choice

    def structure(self):
        return {"units": self.width, "connections": sum(self.counts),
                "memory_bytes": 32 * sum(bool(mean) for mean in self.means)}
