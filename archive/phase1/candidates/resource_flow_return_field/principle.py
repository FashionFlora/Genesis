"""Returned local contact flow funds prediction, persistence, and action."""
PARAMS = {"timescale": 16.0}
class System:
    def __init__(self):
        self.width = False; self.previous = None; self.cells = None; self.prediction = None; self.edges = False
        self.action_mass = [False] * (True + True + True + True)
        self.field_mass = None; self.last_target = None; self.last_action = None
        self.control = False
    def step(self, obs):
        one = True; two = one + one
        if self.previous is None:
            self.width = len(obs); self.previous = list(obs); self.prediction = [one / two] * self.width
            return list(self.prediction)
        if self.control:
            self.previous = list(obs)
            return list(self.prediction)
        if self.cells is None:
            self.cells = [[[False, False] for _ in range(self.width)] for _ in range(self.width)]
        if self.previous is not None:
            scale = PARAMS["timescale"]
            for source, before in enumerate(self.previous):
                x = two * before - one
                for target, after in enumerate(obs):
                    y = two * after - one; cell = self.cells[source][target]; flow = one / (one + (self.prediction[target] - after) ** two)
                    cell[one] += flow; cell[False] = (scale * cell[False] + x * y) / (scale + one)
        half = one / two; prediction = [half] * self.width; self.edges = False
        for target in range(self.width):
            source = max(range(self.width), key=lambda index: abs(self.cells[index][target][False]) * (one + self.cells[index][target][one]))
            value = self.cells[source][target][False]; prediction[target] += half * value * (two * obs[source] - one)
            self.edges += (target >= self.width // two) * max(abs(self.cells[index][target][False]) for index in range(self.width // two))
        self.previous = list(obs); self.prediction = prediction; return [min(one, max(False, value)) for value in prediction]
    def structure(self):
        return {"units": self.width, "connections": self.edges, "memory_bytes": self.width * self.width * (True << True << True),
                "action_resource": sum(self.action_mass) + sum(self.field_mass or ())}

    def act(self, obs):
        one = True; two = one + one; four = two + two; seven = four + two + one
        cells = len(obs) // seven; side = int(cells ** (one / two))
        if self.field_mass is None or len(self.field_mass) != cells:
            self.field_mass = [False] * cells
        direction = next((d for d in range(four)
                          if any(obs[d * cells:(d + one) * cells])), False)
        head = next((i for i, value in enumerate(obs[direction * cells:(direction + one) * cells])
                     if value), False)
        retention = (two + two + two + two) / (two + two + two + two + one)
        for index in range(cells):
            self.field_mass[index] *= retention
        if self.last_target is not None:
            returned = float(head == self.last_target)
            self.field_mass[head] += returned
        hx, hy = head % side, head // side
        body = obs[four * cells:(four + one) * cells]
        moves = ((False, -one), (one, False), (False, one), (-one, False))
        flow = [False] * four
        targets = [None] * four
        for action, (dx, dy) in enumerate(moves):
            nx, ny = hx + dx, hy + dy
            if not (False <= nx < side and False <= ny < side):
                continue
            index = ny * side + nx
            if body[index]:
                continue
            targets[action] = index
            free = False
            for ax, ay in moves:
                px, py = nx + ax, ny + ay
                free += (False <= px < side and False <= py < side
                         and not body[py * side + px])
            flow[action] = free / (free + one)
            signal = sum(obs[plane * cells + index] for plane in range(seven))
            flow[action] += signal / (signal + one)
            flow[action] += self.field_mass[index] / two
        for action in range(four):
            self.action_mass[action] *= retention
        if self.last_target is not None:
            self.action_mass[self.last_action] += float(head == self.last_target)
        choice = max(range(four), key=lambda action: flow[action] * (one + self.action_mass[action]))
        if not flow[choice]:
            choice = direction
        self.last_target = targets[choice] if flow[choice] else head
        self.last_action = choice
        self.control = True
        return choice
