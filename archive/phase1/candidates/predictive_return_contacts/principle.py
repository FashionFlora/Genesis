"""Sparse contacts persist only when their prediction returns information."""

PARAMS = {"timescale": 24.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.history = []
        self.contacts = {}

    @staticmethod
    def _relation(source, target, rows):
        pairs = [(2 * row[source] - 1, 2 * rows[index + 1][target] - 1)
                 for index, row in enumerate(rows[:-1])]
        return sum(left * right for left, right in pairs) / max(1, len(pairs))

    def step(self, obs):
        if self.previous is None:
            self.width = len(obs)
            self.previous = list(obs)
            self.history = [list(obs)]
            return [0.5] * self.width

        prediction = [0.5] * self.width
        for target, contact in list(self.contacts.items()):
            source, resource, count_zero, count_one, positive_zero, positive_one = contact
            state = int(self.previous[source])
            slot = 2 + 2 * state
            estimate = (contact[slot + 1] + 1) / (contact[slot] + 2)
            prediction[target] = estimate
            returned = 1 - abs(estimate - obs[target])
            resource += returned - 0.5
            contact[slot] = PARAMS["timescale"] / (PARAMS["timescale"] + 1) * contact[slot] + 1
            contact[slot + 1] = PARAMS["timescale"] / (PARAMS["timescale"] + 1) * contact[slot + 1] + obs[target]
            contact[1] = resource
            if resource <= 0:
                del self.contacts[target]

        rows = self.history[-int(PARAMS["timescale"]):] + [list(obs)]
        for target in range(self.width):
            if target in self.contacts:
                continue
            source = max(range(self.width), key=lambda item: abs(self._relation(item, target, rows)))
            relation = abs(self._relation(source, target, rows))
            samples = max(1, len(rows) - 1)
            evidence = relation - 1 / samples ** 0.5
            if evidence > 0:
                self.contacts[target] = [source, evidence, 1, 1, 0, 0]

        self.previous = list(obs)
        self.history.append(list(obs))
        self.history = self.history[-int(PARAMS["timescale"]):]
        return prediction

    def structure(self):
        count = len(self.contacts)
        return {"units": count, "connections": count,
                "memory_bytes": count * 48 + self.width * len(self.history) * 8}
