"""Action-conditioned sensory return feeds the reserve that retains it."""


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.previous_action = 0
        self.counts = None
        self.mass = [0.0] * 4
        self.prediction = None
        self.edges = 0.0

    def step(self, obs):
        if self.previous is None:
            self.width = len(obs)
            self.counts = [[[[0.0, 0.0] for _ in range(2)] for _ in range(self.width)] for _ in range(4)]
            self.previous = list(obs)
            self.prediction = [0.5] * self.width
            return list(self.prediction)

        action = self.previous_action
        returned = 0.0
        for target, value in enumerate(obs):
            source_state = int(self.previous[target])
            cell = self.counts[action][target][source_state]
            estimate = (cell[int(value)] + 1.0) / (sum(cell) + 2.0)
            returned += 1.0 - (estimate - value) ** 2
            cell[int(value)] += 1.0

        for index, reserve in enumerate(self.mass):
            self.mass[index] = reserve * reserve / (reserve + 1.0)
        self.mass[action] += returned / self.width

        prediction = [0.5] * self.width
        self.edges = 0.0
        for target in range(self.width):
            candidates = []
            for index in range(4):
                state = int(obs[target])
                cell = self.counts[index][target][state]
                support = abs((cell[1] + 1.0) / (sum(cell) + 2.0) - 0.5) * (sum(cell) + 1.0)
                candidates.append(support)
            chosen = max(range(4), key=lambda index: candidates[index])
            cell = self.counts[chosen][target][int(obs[target])]
            prediction[target] = (cell[1] + 1.0) / (sum(cell) + 2.0)
            self.edges += candidates[chosen]

        self.previous = list(obs)
        self.prediction = prediction
        return list(prediction)

    def act(self, obs):
        action = min(range(4), key=lambda index: self.mass[index])
        self.previous_action = action
        return action

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * 32 + 4 * 8}
