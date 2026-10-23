"""Predictive return is the only currency that creates or removes a contact."""

PARAMS = {"window": 64.0, "probe": 8.0, "birth": 0.12}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.history = []
        self.contacts = {}
        self.baseline = []
        self.tick = 0

    @staticmethod
    def _counts(rows, source, target):
        counts = [[0.0, 0.0], [0.0, 0.0]]
        for before, after in rows:
            state = int(before[source])
            counts[state][0] += 1.0
            counts[state][1] += after[target]
        return counts

    @staticmethod
    def _prob(counts, state):
        count, ones = counts[state]
        return (ones + 1.0) / (count + 2.0)

    @classmethod
    def _loss(cls, rows, counts, source, target):
        return sum((after[target] - cls._prob(counts, int(before[source]))) ** 2
                   for before, after in rows) / max(1, len(rows))

    def _probe(self):
        rows = self.history
        if not rows:
            return
        for target in range(self.width):
            base = self._counts(rows, target, target)
            base_loss = self._loss(rows, base, target, target)
            best = None
            for source in range(self.width):
                if source == target:
                    continue
                counts = self._counts(rows, source, target)
                margin = base_loss - self._loss(rows, counts, source, target)
                if best is None or margin > best[0]:
                    best = (margin, source, counts)
            if best is None or best[0] <= PARAMS["birth"]:
                continue
            margin, source, counts = best
            current = self.contacts.get(target)
            if current is None:
                self.contacts[target] = [source, margin, counts]
            elif source != current[0] and margin > current[1]:
                self.contacts[target] = [source, margin, counts]

    def step(self, obs):
        if self.previous is None:
            self.width = len(obs)
            self.previous = list(obs)
            self.baseline = [[[0.0, 0.0], [0.0, 0.0]] for _ in range(self.width)]
            return [0.5] * self.width

        old = self.previous
        self.history.append((list(old), list(obs)))
        self.history = self.history[-max(1, int(PARAMS["window"])):]
        for target in range(self.width):
            state = int(old[target])
            self.baseline[target][state][0] += 1.0
            self.baseline[target][state][1] += obs[target]

        for target, contact in list(self.contacts.items()):
            source, resource, counts = contact
            edge_p = self._prob(counts, int(old[source]))
            base_p = self._prob(self.baseline[target], int(old[target]))
            actual = obs[target]
            returned = (actual - base_p) ** 2 - (actual - edge_p) ** 2
            counts[int(old[source])][0] += 1.0
            counts[int(old[source])][1] += actual
            resource += returned
            if resource <= 0.0:
                del self.contacts[target]
            else:
                self.contacts[target] = [source, resource, counts]

        self.tick += 1
        if self.tick % max(1, int(PARAMS["probe"])) == 0:
            self._probe()

        prediction = [self._prob(self.baseline[target], int(old[target]))
                      for target in range(self.width)]
        for target, (source, resource, counts) in self.contacts.items():
            confidence = resource / (resource + 1.0)
            value = self._prob(counts, int(old[source]))
            prediction[target] = ((1.0 - confidence) * prediction[target]
                                  + confidence * value)
        self.previous = list(obs)
        return [min(1.0, max(0.0, value)) for value in prediction]

    def structure(self):
        edges = len(self.contacts)
        return {"units": self.width + edges, "connections": edges,
                "memory_bytes": self.width * max(1, int(PARAMS["window"])) * 16 + edges * 80}
