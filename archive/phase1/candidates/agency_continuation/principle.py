"""Action-conditioned prediction and ordering by future viable choices."""

PARAMS = {"memory": 12.0}


class System:
    def __init__(self):
        self.width = 0
        self.last = None
        self.visits = [0.0] * 4
        self.options = [0.0] * 4
        self.steps = 0

    def step(self, obs):
        self.width = len(obs)
        if self.last is not None:
            action, before = self.last
            outcome = self._mobility(obs)
            rate = 1.0 / (self.visits[action] + 1.0)
            self.options[action] += rate * (outcome - self.options[action])
            self.visits[action] += 1.0
        self.last = None
        self.steps += 1
        return [0.5] * self.width

    def _layout(self, obs):
        cells = len(obs) // 7
        side = int(cells ** 0.5)
        direction = next((d for d in range(4)
                          if any(obs[d * cells:(d + 1) * cells])), 0)
        head = next((i for i, value in enumerate(obs[direction * cells:(direction + 1) * cells])
                     if value), 0)
        body = obs[4 * cells:5 * cells]
        return cells, side, direction, head, body

    def _mobility(self, obs):
        cells, side, direction, head, body = self._layout(obs)
        hx, hy = head % side, head // side
        moves = ((0, -1), (1, 0), (0, 1), (-1, 0))
        count = 0
        for dx, dy in moves:
            x, y = hx + dx, hy + dy
            if 0 <= x < side and 0 <= y < side and not body[y * side + x]:
                count += 1
        return count

    def act(self, obs):
        cells, side, direction, head, body = self._layout(obs)
        hx, hy = head % side, head // side
        moves = ((0, -1), (1, 0), (0, 1), (-1, 0))
        scores = []
        for action, (dx, dy) in enumerate(moves):
            x, y = hx + dx, hy + dy
            if action == (direction + 2) % 4 or not (0 <= x < side and 0 <= y < side):
                scores.append(-1.0)
                continue
            index = y * side + x
            if body[index]:
                scores.append(-1.0)
                continue
            future = 0
            for ax, ay in moves:
                nx, ny = x + ax, y + ay
                if 0 <= nx < side and 0 <= ny < side and not body[ny * side + nx]:
                    future += 1
            learned = self.options[action]
            confidence = self.visits[action] / (self.visits[action] + PARAMS["memory"])
            scores.append((1.0 - confidence) * future + confidence * learned)
        choice = max(range(4), key=lambda action: scores[action])
        if scores[choice] < 0:
            choice = direction
        self.last = (choice, self._mobility(obs))
        return choice

    def structure(self):
        return {"units": self.width, "connections": sum(self.visits),
                "memory_bytes": 64}
