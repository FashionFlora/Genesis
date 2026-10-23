"""Intervention closure: retain actions whose observed effects stay controllable."""

PARAMS = {"timescale": 16.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.last_action = None
        self.last_target = None
        self.mass = [1.0] * 4
        self.error = [0.5] * 4
        self.trials = [0.0] * 4
        self.options = 0.0
        self.age = 0

    def step(self, obs):
        if not self.width:
            self.width = len(obs)
            self.previous = list(obs)
            return [0.5] * self.width
        if self.last_action is not None:
            changed = sum(a != b for a, b in zip(self.previous, obs)) / max(1, self.width)
            self.error[self.last_action] = (
                PARAMS["timescale"] * self.error[self.last_action] + changed
            ) / (PARAMS["timescale"] + 1.0)
            cells = self.width // 7
            direction = next((d for d in range(4) if any(obs[d * cells:(d + 1) * cells])), 0)
            head = next((i for i, value in enumerate(obs[direction * cells:(direction + 1) * cells]) if value), 0)
            self.mass[self.last_action] = (
                PARAMS["timescale"] * self.mass[self.last_action]
                + float(self.last_target == head)
            ) / (PARAMS["timescale"] + 1.0)
            self.trials[self.last_action] += 1.0
        self.previous = list(obs)
        self.age += 1
        return [0.5] * self.width

    def _layout(self, obs):
        cells = len(obs) // 7
        side = int(cells ** 0.5)
        direction = next((d for d in range(4) if any(obs[d * cells:(d + 1) * cells])), 0)
        head = next((i for i, value in enumerate(obs[direction * cells:(direction + 1) * cells]) if value), 0)
        body = obs[4 * cells:5 * cells]
        return cells, side, direction, head, body

    def act(self, obs):
        cells, side, direction, head, body = self._layout(obs)
        hx, hy = head % side, head // side
        moves = ((0, -1), (1, 0), (0, 1), (-1, 0))
        scores = [-1.0] * 4
        targets = [None] * 4
        for action, (dx, dy) in enumerate(moves):
            if action == (direction + 2) % 4:
                continue
            nx, ny = hx + dx, hy + dy
            if not (0 <= nx < side and 0 <= ny < side):
                continue
            target = ny * side + nx
            if body[target]:
                continue
            targets[action] = target
            free = sum(
                0 <= nx + ax < side and 0 <= ny + ay < side
                and not body[(ny + ay) * side + nx + ax]
                for ax, ay in moves
            )
            closure = self.mass[action] / (self.error[action] + 0.25)
            confidence = self.trials[action] / (self.trials[action] + PARAMS["timescale"])
            scores[action] = closure * (1.0 + free / 4.0) * (0.5 + confidence)
        choice = max(range(4), key=scores.__getitem__)
        if scores[choice] < 0:
            choice = direction
        self.last_action = choice
        self.last_target = targets[choice] if targets[choice] is not None else head
        self.options = max(scores)
        return choice

    def structure(self):
        return {"units": self.width, "connections": sum(self.trials),
                "memory_bytes": 16 * self.width, "action_closure": sum(self.mass)}
