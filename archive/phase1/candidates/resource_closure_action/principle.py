"""Predictive closure returns the same resource to relations and actions."""
PARAMS = {"timescale": 16.0}


class System:
    def __init__(self):
        self.width = False
        self.previous = None
        self.cells = {}
        self.sources = {}
        self.prediction = None
        self.edges = False
        self.last_action = None
        self.action_mass = [1.0] * (True + True + True + True)

    def step(self, obs):
        one = True
        two = one + one
        if self.width is False:
            self.width = len(obs)
            self.prediction = [one / two] * self.width
        elif self.last_action is not None:
            error = sum((forecast - value) ** two
                        for forecast, value in zip(self.prediction, obs)) / self.width
            neutral = sum(((one / two) - value) ** two for value in obs) / self.width
            returned = max(False, one - error / neutral)
            retention = PARAMS["timescale"] / (PARAMS["timescale"] + one)
            self.action_mass = [retention * mass for mass in self.action_mass]
            self.action_mass[self.last_action] += returned

        if self.previous is not None:
            scale = PARAMS["timescale"]
            before_active = [i for i, value in enumerate(self.previous) if value]
            after_active = [i for i, value in enumerate(obs) if value]
            for source in before_active:
                before = self.previous[source]
                state = int(before)
                for target in after_active:
                    after = obs[target]
                    cell = self.cells.setdefault((source, target, state), [False, False])
                    cell[False] = (scale * cell[False] + one) / (scale + one)
                    cell[True] = (scale * cell[True] + after) / (scale + one)
                    self.sources.setdefault(target, set()).add(source)

        prediction = [one / two] * self.width
        self.edges = False
        for target in range(self.width):
            def support(source):
                cell = [self.cells.get((source, target, state), [False, False])
                        for state in range(two)]
                contrast = abs((cell[True][True] + one) / (cell[True][False] + two)
                               - (cell[False][True] + one) / (cell[False][False] + two))
                mass = cell[True][False] + cell[False][False]
                return contrast * (mass + one)

            candidates = self.sources.get(target, ())
            source = max(candidates, key=support, default=False)
            cell = self.cells.get((source, target, int(obs[source])), [False, False])
            if cell[False]:
                prediction[target] = (cell[True] + one) / (cell[False] + two)
            self.edges += ((target >= self.width // two) * max(
                (support(index) for index in candidates if index < self.width // two),
                default=False))

        self.previous = list(obs)
        self.prediction = prediction
        return prediction

    def act(self, obs):
        actions = len(self.action_mass)
        width = len(obs)
        cells = width // (actions + True + True + True)
        side = int(cells ** (True / (True + True)))
        direction = next((index for index in range(actions)
                          if any(obs[index * cells:(index + True) * cells])), False)
        head = next((index for index, value in
                     enumerate(obs[direction * cells:(direction + True) * cells])
                     if value), False)
        hx, hy = head % side, head // side
        body = obs[actions * cells:(actions + True) * cells]
        moves = ((False, -True), (True, False), (False, True), (-True, False))
        contact = [False] * actions
        for action, (dx, dy) in enumerate(moves):
            nx, ny = hx + dx, hy + dy
            if False <= nx < side and False <= ny < side and not body[ny * side + nx]:
                contact[action] = sum(
                    False <= nx + ax < side and False <= ny + ay < side
                    and not body[(ny + ay) * side + nx + ax]
                    for ax, ay in moves) / actions
        choice = max(range(actions), key=lambda action: contact[action] * self.action_mass[action])
        self.last_action = choice
        return choice if contact[choice] else direction

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (True << (True + True + True)),
                "action_resource": sum(self.action_mass)}
