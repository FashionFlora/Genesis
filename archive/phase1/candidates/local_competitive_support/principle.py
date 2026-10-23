"""One locally budgeted coactivity state is edge strength and persistence."""

PARAMS = {"learning_rate": 1.0, "support_budget": 4}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.support = None
        self.edges = 0

    def _project(self, values):
        budget = PARAMS["support_budget"]
        allocation = [max(0, int(value + 0.5)) for value in values]
        while sum(allocation) > budget:
            candidates = [index for index, amount in enumerate(allocation) if amount]
            index = min(candidates,
                        key=lambda item: 2 * (values[item] - allocation[item]) + 1)
            allocation[index] -= 1
        return allocation

    def step(self, observation):
        if self.support is None:
            self.width = len(observation)
            self.support = [[0] * self.width for _ in range(self.width)]
        if self.previous is not None:
            rate = PARAMS["learning_rate"]
            for source, before in enumerate(self.previous):
                products = [before * after for after in observation]
                mean = sum(products) / self.width
                values = [self.support[source][target] + rate *
                          (products[target] - mean)
                          for target in range(self.width)]
                self.support[source] = self._project(values)
        prediction = [0.5] * self.width
        self.edges = 0
        for target in range(self.width):
            mass = sum(self.support[source][target]
                       for source in range(self.width))
            active = sum(self.support[source][target] * self.previous[source]
                         for source in range(self.width)) if self.previous else 0
            if mass:
                prediction[target] = active / mass
            self.edges += int(any(self.support[source][target]
                                  for source in range(self.width)))
        self.previous = list(observation)
        return [min(1.0, max(0.0, value)) for value in prediction]

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * 8}
