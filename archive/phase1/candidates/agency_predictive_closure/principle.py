"""Choose interventions that are repeatable and preserve later choices."""

PARAMS = {"memory": 8.0}


class System:
    def __init__(self):
        self.width = 0
        self.last = None
        self.counts = [[0.0] * 4 for _ in range(4)]
        self.means = [[[] for _ in range(4)] for _ in range(4)]
        self.energy = [[0.0] * 4 for _ in range(4)]
        self.returned = [[0.0] * 4 for _ in range(4)]

    def step(self, obs):
        self.width = len(obs)
        if self.last is not None:
            action, context, before = self.last
            delta = [value - old for value, old in zip(obs, before)]
            count = self.counts[context][action] + 1.0
            rate = 1.0 / count
            mean = self.means[context][action]
            if not mean:
                mean = [0.0] * self.width
            self.means[context][action] = [old + rate * (change - old)
                                           for old, change in zip(mean, delta)]
            energy = sum(change * change for change in delta)
            self.energy[context][action] += rate * (energy - self.energy[context][action])
            mobility = self._mobility(obs)
            self.returned[context][action] += rate * (
                mobility - self.returned[context][action])
            self.counts[context][action] = count
        self.last = None
        return [0.5] * self.width

    def _layout(self, obs):
        cells = len(obs) // 7
        side = int(cells ** 0.5)
        maps = [obs[index * cells:(index + 1) * cells] for index in range(7)]
        direction = next((d for d in range(4) if any(maps[d])), 0)
        head = next((i for i, value in enumerate(maps[direction]) if value), 0)
        return side, direction, head, maps[4]

    def _context(self, side, head, body):
        x, y = head % side, head // side
        moves = ((0, -1), (1, 0), (0, 1), (-1, 0))
        free = sum(0 <= x + dx < side and 0 <= y + dy < side
                   and not body[(y + dy) * side + x + dx]
                   for dx, dy in moves)
        return min(3, free)

    def _mobility(self, obs):
        side, direction, head, body = self._layout(obs)
        x, y = head % side, head // side
        moves = ((0, -1), (1, 0), (0, 1), (-1, 0))
        return sum(0 <= x + dx < side and 0 <= y + dy < side
                   and not body[(y + dy) * side + x + dx]
                   for dx, dy in moves)

    def _future_mobility(self, side, head, target, body):
        x, y = target % side, target // side
        old_x, old_y = head % side, head // side
        moves = ((0, -1), (1, 0), (0, 1), (-1, 0))
        return sum(0 <= x + dx < side and 0 <= y + dy < side
                   and (x + dx, y + dy) != (old_x, old_y)
                   and not body[(y + dy) * side + x + dx]
                   for dx, dy in moves)

    def act(self, obs):
        side, direction, head, body = self._layout(obs)
        context = self._context(side, head, body)
        x, y = head % side, head // side
        moves = ((0, -1), (1, 0), (0, 1), (-1, 0))
        legal = []
        future = {}
        for action, (dx, dy) in enumerate(moves):
            nx, ny = x + dx, y + dy
            if action == (direction + 2) % 4 or not (0 <= nx < side and 0 <= ny < side):
                continue
            target = ny * side + nx
            if body[target]:
                continue
            legal.append(action)
            future[action] = self._future_mobility(side, head, target, body)
        if not legal:
            self.last = (direction, context, list(obs))
            return direction
        scores = []
        for action in legal:
            mean = self.means[context][action]
            predictable = sum(value * value for value in mean)
            denominator = max(self.energy[context][action], 1.0 / PARAMS["memory"]) ** 0.5
            return_mobility = self.returned[context][action]
            # Untried actions are ordered by present viability; learned return
            # multiplies the same signal once an intervention has been observed.
            closure = (predictable / denominator) * (1.0 + return_mobility)
            scores.append(closure + future[action] /
                          (PARAMS["memory"] * (1.0 + self.counts[context][action])))
        choice = legal[max(range(len(legal)), key=scores.__getitem__)]
        self.last = (choice, context, list(obs))
        return choice

    def structure(self):
        return {"units": self.width,
                "connections": sum(sum(row) for row in self.counts),
                "memory_bytes": 64 * sum(bool(mean) for row in self.means for mean in row)}
