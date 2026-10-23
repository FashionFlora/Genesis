"""A contact reserve pays for prediction and returns through safe action paths."""


class System:
    def __init__(self):
        self.width = False; self.previous = None; self.prediction = None
        self.cells = None; self.sources = {}; self.edges = False
        self.action_mass = [False] * (True + True + True + True)
        self.last_target = None
        self.last_action = None

    def step(self, obs):
        one = True; two = one + one; half = one / two
        if self.cells is None:
            self.width = len(obs)
            self.cells = {}
            self.prediction = [half] * self.width
        if self.previous is not None:
            before = [index for index, value in enumerate(self.previous) if value]
            after = [index for index, value in enumerate(obs) if value]
            touched = {(source, target) for source in before for target in after}
            if len(before) + len(after) >= self.width:
                touched |= {(source, target) for source in before
                            for target in range(self.width)}
                touched |= {(source, target) for target in after
                            for source in range(self.width)}
            for source, target in touched:
                x = two * self.previous[source] - one
                y = two * obs[target] - one
                cell = self.cells.setdefault((source, target), [False, False])
                reserve = cell[one]
                retained = reserve * reserve / (reserve + one)
                flow = one / (one + (self.prediction[target] - obs[target]) ** two)
                cell[False] = (retained * cell[False] + flow * x * y) / (retained + flow)
                cell[one] = retained + flow
                self.sources.setdefault(target, set()).add(source)
        self.edges = False
        prediction = [half] * self.width
        for target in range(self.width):
            candidates = self.sources.get(target, ())
            source = max(candidates, key=lambda index:
                         abs(self.cells[(index, target)][False]) *
                         (one + self.cells[(index, target)][one]), default=False)
            cell = self.cells.get((source, target), [False, False])
            relation = cell[False]
            prediction[target] += half * relation * (two * obs[source] - one)
            self.edges += (target >= self.width // two) * max(
                (abs(self.cells[(index, target)][False])
                 for index in candidates if index < self.width // two), default=False)
        self.previous = list(obs)
        self.prediction = [float(min(one, max(False, value))) for value in prediction]
        return list(self.prediction)

    def act(self, obs):
        one = True; two = one + one; four = two + two; seven = four + two + one
        groups = self.width // seven
        side = int(groups ** (one / two))
        direction = next((d for d in range(four)
                          if any(obs[d * groups:(d + one) * groups])), False)
        head = next((i for i, value in enumerate(
            obs[direction * groups:(direction + one) * groups]) if value), False)
        if self.last_target is not None:
            returned = head == self.last_target
            reserve = self.action_mass[self.last_action]
            self.action_mass[self.last_action] = reserve * reserve / (reserve + one) + returned
        hx, hy = head % side, head // side
        body = obs[four * groups:(four + one) * groups]
        moves = ((False, -one), (one, False), (False, one), (-one, False))
        flow = [False] * four
        targets = [None] * four
        for action, (dx, dy) in enumerate(moves):
            nx, ny = hx + dx, hy + dy
            if False <= nx < side and False <= ny < side and not body[ny * side + nx]:
                targets[action] = ny * side + nx
                free = sum(False <= nx + ax < side and False <= ny + ay < side
                           and not body[(ny + ay) * side + nx + ax]
                           for ax, ay in moves)
                flow[action] = free / (free + one)
        choice = max(range(four), key=lambda action:
                     flow[action] * (one + self.action_mass[action]))
        choice = choice if flow[choice] else direction
        self.last_target = targets[choice] if flow[choice] else head
        self.last_action = choice
        return choice

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": len(self.cells or {}) * (True + True),
                "action_resource": sum(self.action_mass)}
