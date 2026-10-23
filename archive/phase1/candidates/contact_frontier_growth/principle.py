"""A contact keeps the resource it predicts; unused contacts dissolve."""

PARAMS = {"decay": 1.0, "history": 8.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.contacts = {}
        self.cursor = {}
        self.history = []

    def step(self, obs):
        if not self.width:
            self.width = len(obs)
        if self.previous is None:
            self.previous = list(obs)
            self.history.append(list(obs))
            return [0.5] * self.width

        # Each target has one resource-bearing contact.  The same resource
        # both renews a predictive contact and removes an unproductive one.
        for target, contact in list(self.contacts.items()):
            source, resource, correlation = contact
            x = 2.0 * self.previous[source] - 1.0
            y = 2.0 * obs[target] - 1.0
            correlation = (resource * correlation + x * y) / (resource + 1.0)
            resource = resource * resource / (resource + PARAMS["decay"])
            resource += correlation * correlation * obs[target]
            if resource <= PARAMS["decay"]:
                del self.contacts[target]
            else:
                self.contacts[target] = [source, resource, correlation]

        # A vacant target grows its next contact at the frontier of sources.
        # Cycling makes every source observable without retaining all pairs.
        for target in range(self.width):
            if target not in self.contacts and obs[target] >= 0.5:
                samples = self.history[-int(PARAMS["history"]):]
                source = max(range(self.width), key=lambda candidate:
                             abs(sum((2.0 * row[candidate] - 1.0)
                                     * (2.0 * row[target] - 1.0)
                                     for row in samples) / len(samples)))
                self.cursor[target] = source
                x = 2.0 * self.previous[source] - 1.0
                y = 2.0 * obs[target] - 1.0
                correlation = sum((2.0 * row[source] - 1.0)
                                  * (2.0 * row[target] - 1.0)
                                  for row in samples) / len(samples)
                self.contacts[target] = [source, 1.0, correlation]

        prediction = [0.5] * self.width
        for target, (source, _resource, correlation) in self.contacts.items():
            confidence = abs(correlation)
            contact_prediction = 0.5 + 0.5 * correlation * (2.0 * obs[source] - 1.0)
            prediction[target] = ((1.0 - confidence) * prediction[target]
                                  + confidence * contact_prediction)
        self.previous = list(obs)
        self.history.append(list(obs))
        self.history = self.history[-int(PARAMS["history"]):]
        return [min(1.0, max(0.0, value)) for value in prediction]

    def structure(self):
        return {"units": len(self.contacts), "connections": len(self.contacts),
                "memory_bytes": len(self.contacts) * 40 + self.width * (8 + 8 * int(PARAMS["history"]))}
