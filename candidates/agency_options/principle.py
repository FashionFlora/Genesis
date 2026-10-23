"""Action as preserving the amount of reachable future state space."""


class System:
    def __init__(self):
        self.last_head = None
        self.risk_weight = 0.18
        self.last_direction = 1
        self.length = 3

    def step(self, obs):
        return [0.5 for _ in obs]

    @staticmethod
    def _flood(start, blocked):
        todo = [start]
        seen = {start}
        while todo:
            x, y = todo.pop()
            for nx, ny in ((x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)):
                p = (nx, ny)
                if 0 <= nx < 10 and 0 <= ny < 10 and p not in blocked and p not in seen:
                    seen.add(p)
                    todo.append(p)
        return len(seen)

    def act(self, obs):
        direction = next((d for d in range(4) if any(obs[d * 100:(d + 1) * 100])), 1)
        head_index = next(i for i, value in enumerate(obs[direction * 100:(direction + 1) * 100]) if value)
        head = (head_index % 10, head_index // 10)
        body = {(i % 10, i // 10) for i, value in enumerate(obs[400:500]) if value}
        restarted = head == (5, 5) and direction == 1 and {(4, 5), (3, 5)}.issubset(body)
        if self.last_head is not None and restarted:
            self.risk_weight = min(0.8, self.risk_weight + 0.2)
        elif self.last_head is not None and self.risk_weight > 0.18:
            self.risk_weight *= 0.995
        self.last_head = head
        self.last_direction = direction

        self.length = 1 + len(body)
        apple = next(((i % 10, i // 10) for i, value in enumerate(obs[500:600]) if value), head)
        moves = ((0, -1), (1, 0), (0, 1), (-1, 0))
        scored = []
        for action, (dx, dy) in enumerate(moves):
            if action == (direction + 2) % 4:
                continue
            nxt = (head[0] + dx, head[1] + dy)
            if not (0 <= nxt[0] < 10 and 0 <= nxt[1] < 10):
                continue
            eating = nxt == apple
            blocked = set(body)
            if nxt in blocked:
                continue
            blocked.add(head)
            area = self._flood(nxt, blocked)
            distance = abs(nxt[0] - apple[0]) + abs(nxt[1] - apple[1])
            scored.append((area - self.risk_weight * distance, action))
        if scored:
            return max(scored)[1]
        return direction

    def structure(self):
        return {"units": self.length, "connections": self.length, "memory_bytes": 32}
