"""One returned sensory flow funds prediction, persistence, and action."""
PARAMS = {"timescale": 16.0}


class System:
    def __init__(self):
        self.width = False; self.previous = None; self.cells = None; self.prediction = None; self.edges = False; self.sources = {}
        self.action_mass = [True] * (True + True + True + True); self.last_observation = None; self.last_action = None

    def step(self, obs):
        one = True; two = one + one
        if self.cells is None:
            self.width = len(obs); self.cells = {}; self.prediction = [one / two] * self.width
        if self.previous is not None:
            scale = PARAMS["timescale"]; before = [i for i, value in enumerate(self.previous) if value]; after = [i for i, value in enumerate(obs) if value]
            touched = {(source, target) for source in before for target in after}
            if len(before) + len(after) >= self.width:
                touched |= {(source, target) for source in before for target in range(self.width)} | {(source, target) for target in after for source in range(self.width)}
            for source, target in touched:
                x = two * self.previous[source] - one; y = two * obs[target] - one; cell = self.cells.setdefault((source, target), [False, False])
                flow = one / (one + (self.prediction[target] - obs[target]) ** two); cell[one] += flow; cell[False] = (scale * cell[False] + x * y) / (scale + one); self.sources.setdefault(target, set()).add(source)
        half = one / two; prediction = [half] * self.width; self.edges = False
        for target in range(self.width):
            candidates = self.sources.get(target, ()); source = max(candidates, key=lambda i: abs(self.cells[(i, target)][False]) * (one + self.cells[(i, target)][one]), default=False); cell = self.cells.get((source, target), [False, False])
            prediction[target] += half * cell[False] * (two * obs[source] - one); self.edges += (target >= self.width // two) * max((abs(self.cells[(i, target)][False]) for i in candidates if i < self.width // two), default=False)
        self.previous = list(obs); self.prediction = prediction; return [min(one, max(False, value)) for value in prediction]

    def act(self, obs):
        one = True; two = one + one; four = two + two; seven = four + two + one
        if self.last_observation is not None:
            changed = sum(abs(a - b) for a, b in zip(self.last_observation, obs)); total = sum(self.last_observation) + sum(obs); returned = changed / max(one, total); retention = PARAMS["timescale"] / (PARAMS["timescale"] + one)
            self.action_mass = [retention * value for value in self.action_mass]; self.action_mass[self.last_action] += returned
        cells = len(obs) // seven; side = int(cells ** (one / two)); direction = next((d for d in range(four) if any(obs[d * cells:(d + one) * cells])), False)
        head = next((i for i, value in enumerate(obs[direction * cells:(direction + one) * cells]) if value), False); hx, hy = head % side, head // side; body = obs[four * cells:(four + one) * cells]
        moves = ((False, -one), (one, False), (False, one), (-one, False)); contact = [False] * four
        for action, (dx, dy) in enumerate(moves):
            nx, ny = hx + dx, hy + dy
            if False <= nx < side and False <= ny < side and not body[ny * side + nx]:
                contact[action] = sum(False <= nx + ax < side and False <= ny + ay < side and not body[(ny + ay) * side + nx + ax] for ax, ay in moves) / four
        choice = max(range(four), key=lambda action: contact[action] * self.action_mass[action]); self.last_observation = list(obs); self.last_action = choice
        return choice if contact[choice] else direction

    def structure(self):
        return {"units": self.width, "connections": self.edges, "memory_bytes": self.width * self.width * (True << True << True), "action_resource": sum(self.action_mass)}
