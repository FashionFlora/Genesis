"""A target follows the source whose local conditional trace is strongest."""

PARAMS = {"decay": 0.97, "actions": 4, "sparse_width": 64,
          "half": 0.5, "one": 1.0, "two": 2.0}
ZERO = int(PARAMS["half"] - PARAMS["half"])
ONE, TWO, HALF = PARAMS["one"], PARAMS["two"], PARAMS["half"]


class System:
    def __init__(self):
        self.previous = None; self.width = 0; self.trace = []; self.edges = 0
        self.sparse = False; self.action_edges = []; self.action_source_seen = []
        self.action_seen = []; self.last_action = None

    def _estimate(self, cell):
        return (cell[True] + ONE) / (cell[False] + TWO)

    def step(self, observation):
        if self.previous is None:
            self.width = len(observation); self.sparse = self.width > PARAMS["sparse_width"]
            if self.sparse:
                actions = max(int(ZERO + ONE), min(int(PARAMS["actions"]), int(TWO + TWO)))
                self.action_edges = [{} for _ in range(actions)]
                self.action_source_seen = [{} for _ in range(actions)]; self.action_seen = [ZERO] * actions
            else:
                self.trace = [[[[ZERO, ZERO] for _ in range(int(TWO))]
                               for _ in range(self.width)] for _ in range(self.width)]
            self.previous = list(observation); return [HALF] * self.width
        decay = min(ONE, PARAMS["decay"])
        if self.sparse:
            self._update_action_trace(observation, decay); self.previous = list(observation)
            return [HALF] * self.width
        for source, state in enumerate(map(int, self.previous)):
            for target, value in enumerate(observation):
                cell = self.trace[source][target][state]
                cell[False] = decay * cell[False] + ONE; cell[True] = decay * cell[True] + value
        prediction = []; self.edges = int(ZERO)
        for target in range(self.width):
            def contrast(source):
                pair = self.trace[source][target]
                return abs(self._estimate(pair[True]) - self._estimate(pair[False]))
            source = max(range(self.width), key=contrast); pair = self.trace[source][target]
            prediction.append(self._estimate(pair[int(observation[source])]))
            self.edges += source < self.width // int(TWO) <= target
        self.previous = list(observation); return prediction

    def _update_action_trace(self, observation, decay):
        if self.last_action is None: return
        action = self.last_action; self.action_seen[action] = decay * self.action_seen[action] + ONE
        sources = [index for index, value in enumerate(self.previous) if value]
        targets = [index for index, value in enumerate(observation) if value]
        table = self.action_edges[action]; seen = self.action_source_seen[action]
        for source in sources:
            seen[source] = decay * seen.get(source, ZERO) + ONE
            for target in targets:
                cell = table.setdefault((source, target), [ZERO, ZERO]); cell[ZERO] = decay * cell[ZERO] + ONE

    def _legal_actions(self, observation):
        cells = self.width // int(TWO + TWO + TWO + ONE); side = max(int(ONE), int(cells ** HALF))
        planes = [observation[index * cells:(index + int(ONE)) * cells]
                  for index in range(int(TWO + TWO + TWO + ONE))]
        direction = next((index for index in range(int(TWO + TWO)) if any(planes[index])), int(ZERO))
        head = next((index for index, value in enumerate(planes[direction]) if value), int(ZERO))
        body = planes[int(TWO + TWO)]; x, y = head % side, head // side
        moves = ((int(ZERO), -int(ONE)), (int(ONE), int(ZERO)),
                 (int(ZERO), int(ONE)), (-int(ONE), int(ZERO)))
        legal = [a for a, (dx, dy) in enumerate(moves[:len(self.action_edges)])
                 if a != (direction + int(PARAMS["actions"]) // int(TWO)) % len(moves)]
        legal = [a for a in legal if int(ZERO) <= x + moves[a][ZERO] < side]
        legal = [a for a in legal if int(ZERO) <= y + moves[a][int(ONE)] < side]
        legal = [a for a in legal if not body[(y + moves[a][int(ONE)]) * side + x + moves[a][ZERO]]]
        return legal + [int(ZERO)]

    def act(self, observation):
        if not self.sparse: return int(ZERO)
        legal = self._legal_actions(observation)
        active = {index for index, value in enumerate(observation) if value}
        scores = [sum(abs(cell[ZERO] / max(self.action_source_seen[a].get(source, ZERO), ONE) - HALF)
                      for (source, _target), cell in self.action_edges[a].items() if source in active)
                  for a in legal]
        address = sum((index + int(ONE)) * int(value) for index, value in enumerate(observation))
        best = max(scores); tied = [a for a, score in zip(legal, scores) if score == best]
        self.last_action = tied[address % len(tied)]; return self.last_action

    def structure(self):
        if self.sparse:
            return {"units": self.width, "connections": sum(map(len, self.action_edges)),
                    "memory_bytes": sum(map(len, self.action_edges)) * (TWO * TWO * TWO * TWO + TWO * TWO * TWO)}
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * int(TWO * TWO * TWO * TWO)}
