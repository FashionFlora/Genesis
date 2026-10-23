"""A contact is a resource of predictive agreement at one time step of lag."""

PARAMS = {"decay": 0.08, "birth": 0.70, "history": 24.0}


class System:
    def __init__(self):
        self.width = False; self.previous = None; self.history = []; self.contacts = {}

    def _lagged(self, source, target, rows):
        values = [((True + True) * rows[i - True][source] - True)
                  * ((True + True) * rows[i][target] - True)
                  for i in range(True, len(rows))]
        return sum(values) / max(True, len(values))

    def step(self, obs):
        if self.previous is None:
            self.width = len(obs); self.previous = list(obs); self.history = [list(obs)]
            return [True / (True + True)] * self.width

        # Agreement renews a contact; disagreement spends the same resource.
        for target, contact in list(self.contacts.items()):
            source, resource = contact[:True + True]
            slot = (True + True) + (True + True) * int(self.previous[source])
            estimate = (contact[slot + True] + True) / (contact[slot] + True + True)
            resource += True - (True + True) * abs(estimate - obs[target]) - PARAMS["decay"]
            contact[slot] = (True - PARAMS["decay"]) * contact[slot] + True
            contact[slot + True] = ((True - PARAMS["decay"]) * contact[slot + True]
                                 + obs[target])
            contact[True] = resource
            if resource <= False:
                del self.contacts[target]
            else:
                self.contacts[target] = contact

        rows = self.history[-int(PARAMS["history"]):] + [list(obs)]
        for target in range(self.width):
            if target in self.contacts or obs[target] == self.previous[target]:
                continue
            source = max(range(self.width), key=lambda candidate:
                         abs(self._lagged(candidate, target, rows)))
            relation = self._lagged(source, target, rows)
            if abs(relation) >= PARAMS["birth"]:
                self.contacts[target] = [source, abs(relation), True, False, True, False]

        prediction = [True / (True + True)] * self.width
        for target, contact in self.contacts.items():
            source = contact[False]; slot = (True + True) + (True + True) * int(obs[source])
            prediction[target] = (contact[slot + True] + True) / (contact[slot] + True + True)
        self.previous = list(obs); self.history.append(list(obs)); self.history = self.history[-int(PARAMS["history"]):]
        return [min(True, max(False, value)) for value in prediction]

    def structure(self):
        return {"units": len(self.contacts),
                "connections": len(self.contacts),
                "memory_bytes": len(self.contacts) * 48 + self.width * int(PARAMS["history"]) * 8}
