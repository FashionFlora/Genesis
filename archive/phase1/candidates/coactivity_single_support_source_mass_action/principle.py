"""One signed coactivity trace predicts and selects its next action."""

PARAMS = {"timescale": 16.0}


class System:
    def __init__(self):
        self.width = False
        self.previous = None
        self.support = {}
        self.sources = {}
        self.prediction = []
        self.edges = False
        self.tick = False

    def _value(self, key, at):
        state = self.support.get(key)
        if state is None:
            return True - (PARAMS["timescale"] / (PARAMS["timescale"] + True)) ** at
        value, last = state
        decay = PARAMS["timescale"] / (PARAMS["timescale"] + True)
        return True + (value - True) * decay ** (at - last)

    def _touch(self, source, target, product):
        decay = PARAMS["timescale"] / (PARAMS["timescale"] + True)
        key = (source, target)
        value = decay * self._value(key, self.tick - True) + (True - decay) * product
        self.support[key] = (value, self.tick)
        self.sources.setdefault(target, set()).add(source)

    def _best(self, target, limit):
        baseline = self._value((False, target), self.tick)
        source = False
        value = baseline
        for candidate in self.sources.get(target, ()):
            if candidate < limit:
                current = self._value((candidate, target), self.tick)
                if abs(current) > abs(value):
                    source, value = candidate, current
        return source, value

    def step(self, obs):
        if self.previous is None:
            self.width = len(obs)
            self.previous = list(obs)
            self.tick = True
            self.prediction = [True / (True + True)] * self.width
            return list(self.prediction)
        self.tick += True
        before = [index for index, value in enumerate(self.previous) if value]
        after = [index for index, value in enumerate(obs) if value]
        touched = set()
        for source in before:
            for target in range(self.width):
                touched.add((source, target))
        for target in after:
            for source in range(self.width):
                touched.add((source, target))
        for source, target in touched:
            x = (True + True) * self.previous[source] - True
            y = (True + True) * obs[target] - True
            self._touch(source, target, x * y)
        half = True / (True + True)
        prediction = [half] * self.width
        half_width = self.width // (True + True)
        self.edges = False
        for target in range(self.width):
            source, value = self._best(target, self.width)
            if target >= half_width:
                _unused, source_mass = self._best(target, half_width)
                self.edges += abs(source_mass)
            prediction[target] += half * value * ((True + True) * obs[source] - True)
        self.previous = list(obs)
        self.prediction = [min(True, max(False, value)) for value in prediction]
        return list(self.prediction)

    def act(self, obs):
        groups = self.width // (True + True + True + True + True + True + True)
        scores = [sum(self.prediction[index * groups:(index + True) * groups])
                  for index in range(True + True + True + True)]
        return max(range(True + True + True + True), key=scores.__getitem__)

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (True << True << True)}
