"""A contact remains only while its prediction pays its maintenance cost."""

PARAMS = {"leak": 0.004, "floor": 0.035, "probe": 12.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.contacts = {}
        self.cursor = {}
        self.baseline = {}

    def _new_contact(self, target):
        source = self.cursor.get(target, target - 1)
        source %= self.width
        self.cursor[target] = (source + 1) % self.width
        return [source, 0.0, [[0.0, 0.0], [0.0, 0.0]], 0.0]

    @staticmethod
    def _prob(stats, state):
        count, ones = stats[state]
        return (ones + 1.0) / (count + 2.0)

    def step(self, obs):
        if self.previous is None:
            self.width = len(obs)
            self.previous = list(obs)
            self.baseline = [[[0.0, 0.0], [0.0, 0.0]]
                             for _ in range(self.width)]
            return [0.5] * self.width

        old = self.previous
        # A candidate is born when a target is active and no retained contact
        # is available.  Its mass and its predictive statistics share one law.
        for target in range(self.width):
            contact = self.contacts.get(target)
            if contact is None:
                contact = self._new_contact(target)
                self.contacts[target] = contact
            source, mass, stats, _gain = contact
            target_stats = self.baseline[target]
            base_p = self._prob(target_stats, int(old[target]))
            edge_p = self._prob(stats, int(old[source]))
            actual = float(obs[target])
            gain = (actual - base_p) ** 2 - (actual - edge_p) ** 2
            mass += gain - PARAMS["leak"]
            target_stats[int(old[target])][0] += 1.0
            target_stats[int(old[target])][1] += actual
            stats[int(old[source])][0] += 1.0
            stats[int(old[source])][1] += actual
            if mass <= PARAMS["floor"]:
                # Depletion is also exploration: the next contact gets a new
                # source, without a separate pruning or growth rule.
                self.contacts[target] = self._new_contact(target)
            else:
                self.contacts[target] = [source, mass, stats, gain]

        prediction = [0.5] * self.width
        for target, contact in self.contacts.items():
            source, mass, stats, _gain = contact
            confidence = min(1.0, mass / PARAMS["probe"])
            value = self._prob(stats, int(old[source]))
            prediction[target] = 0.5 + confidence * (value - 0.5)

        self.previous = list(obs)
        return [min(1.0, max(0.0, value)) for value in prediction]

    def structure(self):
        active = sum(1 for source, mass, stats, gain in self.contacts.values()
                     if mass > PARAMS["floor"])
        return {"units": self.width + active, "connections": active,
                "memory_bytes": self.width * 24 + len(self.contacts) * 96}
