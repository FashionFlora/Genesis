"""Predictive contact spends and renews the resource that keeps an edge alive."""

PARAMS = {"resource_floor": 0.015}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.edges = {}
        self.units = set()

    def step(self, obs):
        if not self.width:
            self.width = len(obs)
        active = {index for index, value in enumerate(obs) if value >= 0.5}
        self.units.update(active)

        # Contact replenishes an edge; unrenewed mass pays the same maintenance cost.
        if self.previous is not None:
            prior = self.previous
            for (source, target), (mass, correlation) in list(self.edges.items()):
                x = 2.0 * prior[source] - 1.0
                y = 2.0 * obs[target] - 1.0
                self.edges[(source, target)][1] = (mass * correlation + x * y) / (mass + 1.0)
        for pair in list(self.edges):
            mass, correlation = self.edges[pair]
            mass = mass * mass / (mass + 1.0)
            if mass <= PARAMS["resource_floor"]:
                del self.edges[pair]
            else:
                self.edges[pair] = [mass, correlation]

        if self.previous is not None:
            before = {index for index, value in enumerate(self.previous) if value >= 0.5}
            for source in before:
                x = 2.0 * self.previous[source] - 1.0
                for target in active:
                    pair = (source, target)
                    mass, correlation = self.edges.get(pair, [0.0, 0.0])
                    self.edges[pair] = [mass + 1.0, correlation]

        prediction = [0.5] * self.width
        incoming = {}
        for (source, target), (mass, correlation) in self.edges.items():
            if source != target and (target not in incoming or
                                     mass * abs(correlation) > incoming[target][0]):
                incoming[target] = (mass * abs(correlation), source, correlation)
        for target, (_, source, correlation) in incoming.items():
            prediction[target] += 0.5 * correlation * (2.0 * obs[source] - 1.0)

        self.previous = list(obs)
        return [min(1.0, max(0.0, value)) for value in prediction]

    def structure(self):
        return {"units": len(self.units), "connections": len(self.edges),
                "memory_bytes": len(self.units) * 8 + len(self.edges) * 64}
