"""One context-action field predicts effects and retains returned control."""

PARAMS = {"timescale": 16.0, "contexts": 8, "uncertainty": 0.1}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.previous_context = 0
        self.last_action = 0
        self.models = {}
        self.successors = {}
        self.last = None

    @staticmethod
    def _context(obs):
        if not obs:
            return 0
        return int(sum((i + 1) * float(v) for i, v in enumerate(obs))) % int(PARAMS["contexts"])

    def _cell(self, context, action):
        key = (context, action)
        if key not in self.models:
            self.models[key] = [0.0, [0.0] * self.width, 0.0]
        return self.models[key]

    def step(self, obs):
        self.width = len(obs)
        context = self._context(obs)
        if self.previous is not None:
            cell = self._cell(self.previous_context, self.last_action)
            count, mean, error = cell
            delta = [float(v) - float(p) for v, p in zip(obs, self.previous)]
            rate = 1.0 / (count + 1.0)
            new_mean = [m + rate * (x - m) for m, x in zip(mean, delta)]
            residual = sum((x - m) ** 2 for x, m in zip(delta, mean)) / max(1, self.width)
            cell[2] = (count * error + residual) / (count + 1.0)
            cell[1] = new_mean
            cell[0] = count + 1.0
            self.successors.setdefault((self.previous_context, self.last_action), {})
            targets = self.successors[(self.previous_context, self.last_action)]
            targets[context] = targets.get(context, 0.0) + 1.0
        self.previous = list(obs)
        self.previous_context = context
        return [0.5] * self.width

    def _capacity(self, context):
        effects = []
        for action in range(4):
            cell = self.models.get((context, action))
            if cell and cell[0] > 0:
                effects.append((cell[1], cell[2], cell[0]))
        if len(effects) < 2:
            return 0.0
        separation = 0.0
        pairs = 0
        for i, (left, _, _) in enumerate(effects):
            for right, _, _ in effects[i + 1:]:
                separation += sum((a - b) ** 2 for a, b in zip(left, right)) / max(1, self.width)
                pairs += 1
        noise = sum(error for _, error, _ in effects) / len(effects)
        confidence = sum(count / (count + PARAMS["timescale"]) for _, _, count in effects) / len(effects)
        return confidence * separation / (pairs * (noise + PARAMS["uncertainty"]))

    def act(self, obs):
        context = self._context(obs)
        scores = []
        for action in range(4):
            successors = self.successors.get((context, action), {})
            total = sum(successors.values())
            returned = (sum(n * self._capacity(next_context)
                            for next_context, n in successors.items()) / total
                        if total else 0.0)
            # Unobserved transitions are sampled in proportion to missing evidence.
            scores.append(returned + PARAMS["timescale"] / (PARAMS["timescale"] + total))
        choice = max(range(4), key=lambda action: scores[action])
        self.last_action = choice
        return choice

    def structure(self):
        return {"units": self.width, "connections": sum(cell[0] for cell in self.models.values()),
                "memory_bytes": 32 * (len(self.models) + sum(len(v) for v in self.successors.values()))}
