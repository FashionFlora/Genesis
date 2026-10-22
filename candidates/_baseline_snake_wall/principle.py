"""Small Snake controller that continues forward and turns away from obstacles."""


class System:
    def step(self, obs):
        return [0.5 for _ in obs]

    def act(self, obs):
        direction = 0
        head = 0
        for value in range(4):
            start = value * 100
            for index in range(100):
                if obs[start + index]:
                    direction = value
                    head = index
                    break
        x = head % 10
        y = head // 10
        body = obs[400:500]
        moves = ((0, -1), (1, 0), (0, 1), (-1, 0))
        for action in (direction, (direction + 1) % 4, (direction - 1) % 4):
            dx, dy = moves[action]
            nx, ny = x + dx, y + dy
            if 0 <= nx < 10 and 0 <= ny < 10 and not body[ny * 10 + nx]:
                return action
        return direction

    def structure(self):
        return {"units": 0, "connections": 0, "memory_bytes": 0}
