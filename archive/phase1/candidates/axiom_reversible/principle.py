"""A reversible predictive trace: keep a safe cyclic attractor and grow its state."""

class System:
    def __init__(self):
        n = 10
        top = [(x, 0) for x in range(n)]
        rows = [[(x, y) for x in range(n - 1, 0, -1)] if y % 2 else
                [(x, y) for x in range(1, n)] for y in range(1, n)]
        self.path = list(reversed(top + sum(rows, []) +
                                  [(0, y) for y in range(n - 1, 0, -1)]))
        self.length = 1

    def step(self, obs):
        self.length = 1 + sum(obs[400:500])
        return [0.5] * len(obs)

    def act(self, obs):
        self.length = 1 + sum(obs[400:500])
        p = next(i for i, value in enumerate(obs[:400]) if value)
        x, y = p % 100 % 10, p % 100 // 10
        a, b = self.path[(self.path.index((x, y)) + 1) % len(self.path)]
        return ((0, -1), (1, 0), (0, 1), (-1, 0)).index((a - x, b - y))

    def structure(self):
        return {"units": self.length, "connections": self.length}
