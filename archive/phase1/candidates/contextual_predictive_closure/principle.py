"""One law: retain transitions that shorten the next sensory description."""

import math


PARAMS = {"timescale": 8.0, "contexts": 8, "actions": 4}
ZERO, ONE, TWO, HALF = 0.0, 1.0, 2.0, 0.5
GLOBAL = object()
EMPTY = (ZERO, ZERO, ZERO)


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.last_action = 0
        self.context = 0
        self.cells = {}
        self.prediction = []
        self.edges = ZERO

    @staticmethod
    def _p(cell):
        return (cell[2] + HALF) / (cell[0] + ONE)

    def _address(self, obs):
        return sum((index + ONE) * int(bit) for index, bit in enumerate(obs)) % max(
            int(PARAMS["contexts"]), int(ONE))

    def _key(self, address, action, source, target, state):
        return address, action, source, target, int(state)

    def step(self, obs):
        if self.previous is None:
            self.width, self.previous = len(obs), list(obs)
            self.prediction = [HALF] * self.width
            return list(self.prediction)
        self.context = self._address(self.previous)
        retention = PARAMS["timescale"] / (PARAMS["timescale"] + ONE)
        for source, state in enumerate(self.previous):
            for target, value in enumerate(obs):
                for address, action in ((GLOBAL, GLOBAL), (self.context, self.last_action)):
                    cell = self.cells.setdefault(self._key(address, action, source, target, state),
                                                 [ZERO, ZERO, ZERO])
                    cell[0] = retention * cell[0] + ONE
                    cell[1] = retention * cell[1] + int(state)
                    cell[2] = retention * cell[2] + value
        prediction, self.edges = [HALF] * self.width, ZERO
        for target in range(self.width):
            source = max(range(self.width), key=lambda s: abs(
                self._p(self.cells.get(self._key(GLOBAL, GLOBAL, s, target, ONE), EMPTY)) -
                self._p(self.cells.get(self._key(GLOBAL, GLOBAL, s, target, ZERO), EMPTY))))
            state = int(obs[source])
            global_cell = self.cells.get(self._key(GLOBAL, GLOBAL, source, target, state), EMPTY)
            local_cell = self.cells.get(self._key(self.context, self.last_action, source, target, state), EMPTY)
            weight = local_cell[0] / (local_cell[0] + global_cell[0] + ONE)
            prediction[target] = (ONE - weight) * self._p(global_cell) + weight * self._p(local_cell)
            self.edges += (target >= self.width // int(TWO)) * abs(
                self._p(self.cells.get(self._key(GLOBAL, GLOBAL, source, target, ONE), EMPTY)) -
                self._p(self.cells.get(self._key(GLOBAL, GLOBAL, source, target, ZERO), EMPTY)))
        self.previous, self.prediction = list(obs), prediction
        return list(prediction)

    def act(self, obs):
        """Use the same field to choose the shortest expected next-state code."""
        actions = max(int(ONE), min(int(4), int(PARAMS["actions"])))
        context, scores = self._address(obs), []
        for action in range(actions):
            code = ZERO
            for target in range(self.width):
                source = max(range(self.width), key=lambda s: abs(
                    self._p(self.cells.get(self._key(context, action, s, target, ONE), EMPTY)) -
                    self._p(self.cells.get(self._key(context, action, s, target, ZERO), EMPTY))))
                p = self._p(self.cells.get(self._key(context, action, source, target,
                                                    int(obs[source])), EMPTY))
                code -= p * math.log(p) + (ONE - p) * math.log(ONE - p)
            scores.append(code)
        best = min(scores)
        tied = [action for action, score in enumerate(scores) if score == best]
        self.last_action = tied[self._address(obs) % len(tied)]
        return self.last_action

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": len(self.cells) * 32}
