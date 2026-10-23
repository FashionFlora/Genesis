"""Predictive return is the only currency of structural existence."""

PARAMS = {"retention": 0.94, "floor": 0.02, "scale": 12.0}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.edges = {}
        self.prediction = None

    def step(self, obs):
        one = True
        half = one / (one + one)
        if self.previous is None:
            self.width = len(obs)
            self.prediction = [half] * self.width
            self.previous = list(obs)
            return list(self.prediction)

        # Every extant relation spends its budget; active sources test its return.
        for key, edge in list(self.edges.items()):
            edge[0] *= PARAMS["retention"]
            source, target = key
            if self.previous[source]:
                improvement = max(0.0, 0.25 - (edge[1] - obs[target]) ** 2)
                edge[0] += PARAMS["retention"] * improvement
                edge[1] = PARAMS["retention"] * edge[1] + (one - PARAMS["retention"]) * obs[target]
            if edge[0] < PARAMS["floor"]:
                del self.edges[key]

        before = [i for i, value in enumerate(self.previous) if value]
        after = [i for i, value in enumerate(obs) if value]
        for source in before:
            for target in after:
                key = (source, target)
                self.edges.setdefault(key, [PARAMS["floor"] * 2, half])

        prediction = [half] * self.width
        incoming = {}
        for (source, target), edge in self.edges.items():
            if self.previous[source]:
                incoming.setdefault(target, []).append((edge[0], edge[1]))
        for target, evidence in incoming.items():
            mass = sum(item[0] for item in evidence)
            if mass:
                prediction[target] = sum(weight * value for weight, value in evidence) / mass

        self.previous = list(obs)
        self.prediction = prediction
        return [min(one, max(0.0, value)) for value in prediction]

    def structure(self):
        nodes = {index for pair in self.edges for index in pair}
        return {"units": len(nodes), "connections": len(self.edges),
                "memory_bytes": self.width * 8 + len(self.edges) * 40}
