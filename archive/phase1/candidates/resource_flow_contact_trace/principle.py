"""A returned contact flow funds prediction, persistence, and action traces."""

PARAMS = {"timescale": 16.0}


class System:
    def __init__(self):
        self.width = False; self.previous = None; self.cells = None
        self.prediction = None; self.edges = False; self.sources = {}
        self.action_mass = [False] * (True + True + True + True)
        self.last_target = None; self.last_action = None

    def step(self, obs):
        one = True; two = one + one
        if self.cells is None:
            self.width = len(obs); self.cells = {}; self.prediction = [one / two] * self.width
        if self.previous is not None:
            scale = PARAMS["timescale"]
            before = [index for index, value in enumerate(self.previous) if value]
            after = [index for index, value in enumerate(obs) if value]
            touched = {(source, target) for source in before for target in after}
            if len(before) + len(after) >= self.width:
                touched |= {(source, target) for source in before for target in range(self.width)}
                touched |= {(source, target) for target in after for source in range(self.width)}
            for source, target in touched:
                x = two * self.previous[source] - one; y = two * obs[target] - one
                cell = self.cells.setdefault((source, target), [False, False])
                flow = one / (one + (self.prediction[target] - obs[target]) ** two)
                cell[one] += flow; cell[False] = (scale * cell[False] + x * y) / (scale + one)
                self.sources.setdefault(target, set()).add(source)
        half = one / two; prediction = [half] * self.width; self.edges = False
        for target in range(self.width):
            candidates = self.sources.get(target, ())
            source = max(candidates, key=lambda index: abs(self.cells[(index, target)][False]) *
                         (one + self.cells[(index, target)][one]), default=False)
            value = self.cells.get((source, target), [False])[False]
            prediction[target] += half * value * (two * obs[source] - one)
            self.edges += (target >= self.width // two) * max(
                (abs(self.cells[(index, target)][False]) for index in candidates
                 if index < self.width // two), default=False)
        self.previous = list(obs); self.prediction = prediction
        return [min(one, max(False, value)) for value in prediction]

    def act(self, obs):
        one = True; two = one + one; four = two + two; seven = four + two + one
        cells = len(obs) // seven; side = int(cells ** (one / two))
        direction = next((d for d in range(four)
                          if any(obs[d * cells:(d + one) * cells])), False)
        head = next((i for i, value in enumerate(obs[direction * cells:(direction + one) * cells])
                     if value), False)
        hx, hy = head % side, head // side
        body = obs[four * cells:(four + one) * cells]
        moves = ((False, -one), (one, False), (False, one), (-one, False))
        if self.last_action is not None:
            hit = float(head == self.last_target)
            retention = PARAMS["timescale"] / (PARAMS["timescale"] + one)
            returned = hit / (one + (one - hit) ** two)
            self.action_mass[self.last_action] = retention * self.action_mass[self.last_action] + returned
        flow = [False] * four; targets = [None] * four
        for action, (dx, dy) in enumerate(moves):
            nx, ny = hx + dx, hy + dy
            if False <= nx < side and False <= ny < side and not body[ny * side + nx]:
                targets[action] = ny * side + nx
                flow[action] = sum(False <= nx + ax < side and False <= ny + ay < side
                                   and not body[(ny + ay) * side + nx + ax] for ax, ay in moves) / four
        choice = max(range(four), key=lambda action: flow[action] *
                     (one + self.action_mass[action]))
        choice = choice if flow[choice] else direction
        self.last_target = targets[choice] if flow[choice] else head
        self.last_action = choice
        return choice

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (True << True << True),
                "action_resource": sum(self.action_mass)}
