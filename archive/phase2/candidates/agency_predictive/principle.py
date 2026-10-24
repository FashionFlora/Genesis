"""Agency from one law: keep interventions that make the next state predictable."""

PARAMS = {"decay": 0.985, "support": 6.0, "memory": 4.0}


class System:
    def __init__(self):
        self.n = 0
        self.previous = None
        self.tables = None
        self.mass = 0

    def _start(self, n):
        self.n = n
        self.tables = [[[[0.0, 0.0] for _ in range(2)] for _ in range(n)] for _ in range(n)]

    def step(self, obs):
        n = len(obs)
        if n > 64:
            self.n = n
            return [0.5] * n
        if self.tables is None:
            self._start(n)
        if n != self.n:
            return [0.5] * n
        values = [float(x) for x in obs]
        if self.previous is not None:
            decay = PARAMS["decay"]
            for row in self.tables:
                for pair in row:
                    for cell in pair:
                        cell[0] *= decay
                        cell[1] *= decay
            for source, bit in enumerate(self.previous):
                for target, value in enumerate(values):
                    cell = self.tables[source][target][bit]
                    cell[0] += 1.0
                    cell[1] += value
        prediction = []
        active = 0
        for target in range(n):
            strength = 0.0
            best_source = -1
            for source in range(n):
                pair = self.tables[source][target]
                estimates = [(cell[1] + 0.5) / (cell[0] + 1.0) for cell in pair]
                score = abs(estimates[1] - estimates[0]) * (pair[0][0] + pair[1][0])
                score /= pair[0][0] + pair[1][0] + PARAMS["support"]
                if score > strength:
                    strength = score
                    best_source = source
            if best_source >= 0:
                cell = self.tables[best_source][target][int(values[best_source] > 0.5)]
                prediction.append((cell[1] + 0.5) / (cell[0] + 1.0))
            else:
                prediction.append(0.5)
            active += int(strength > 0.08 and best_source != target)
        self.previous = [int(value > 0.5) for value in values]
        self.mass = active
        return prediction

    @staticmethod
    def _space(start, blocked, side):
        todo = [start]
        seen = {start}
        while todo:
            x, y = todo.pop()
            for nx, ny in ((x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)):
                point = (nx, ny)
                if 0 <= nx < side and 0 <= ny < side and point not in blocked and point not in seen:
                    seen.add(point)
                    todo.append(point)
        return len(seen)

    def act(self, obs):
        n = len(obs)
        side = int((n / 7.0) ** 0.5)
        if side * side * 7 != n:
            return int(sum(float(x) for x in obs) % 4)
        area = side * side
        direction = next((d for d in range(4) if any(obs[d * area:(d + 1) * area])), 1)
        head_index = next((i for i, value in enumerate(obs[direction * area:(direction + 1) * area]) if value), 0)
        head = (head_index % side, head_index // side)
        body = {(i % side, i // side) for i, value in enumerate(obs[4 * area:5 * area]) if value}
        target = next(((i % side, i // side) for i, value in enumerate(obs[5 * area:6 * area]) if value), head)
        moves = ((0, -1), (1, 0), (0, 1), (-1, 0))
        options = []
        for action, (dx, dy) in enumerate(moves):
            if action == (direction + 2) % 4:
                continue
            nxt = (head[0] + dx, head[1] + dy)
            if not (0 <= nxt[0] < side and 0 <= nxt[1] < side) or nxt in body:
                continue
            blocked = set(body)
            blocked.add(head)
            reachable = self._space(nxt, blocked, side)
            distance = abs(nxt[0] - target[0]) + abs(nxt[1] - target[1])
            options.append((reachable - 0.18 * distance, action))
        return max(options)[1] if options else direction

    def structure(self):
        return {"units": self.mass, "connections": self.mass * self.mass,
                "memory_bytes": self.n * self.n * 16 if self.tables else 0}
