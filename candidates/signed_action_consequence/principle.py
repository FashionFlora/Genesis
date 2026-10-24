"""Signed local action consequences for the organism world."""


class System:
    def __init__(self):
        self.width = 0

    def step(self, obs):
        self.width = len(obs)
        return [0.5 for _ in obs]

    def structure(self):
        return {"units": self.width, "connections": self.width * 3}
