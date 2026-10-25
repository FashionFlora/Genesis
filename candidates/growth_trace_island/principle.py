"""A temporal association grows with repeated evidence and fades without it."""


class System:
    def __init__(self):
        self.decay = 0.97
        self.previous = None
        self.edges = {}

    def step(self, obs):
        if self.previous is None:
            self.previous = list(obs)
            return [0.5] * len(obs)
        for source, value in enumerate(self.previous):
            for target, outcome in enumerate(obs):
                edge = self.edges.get((source, int(value)))
                if edge is None:
                    edge = {}
                    self.edges[(source, int(value))] = edge
                count, total = edge.get(target, (0.0, 0.0))
                edge[target] = (count * self.decay + 1.0,
                                total * self.decay + float(outcome))
        prediction = []
        for target in range(len(obs)):
            estimates = []
            for source, value in enumerate(obs):
                edge = self.edges.get((source, int(value)), {}).get(target)
                estimates.append((edge[1] + 1.0) / (edge[0] + 2.0)
                                  if edge else 0.5)
            prediction.append(sum(estimates) / len(estimates))
        stale = []
        for key, edge in self.edges.items():
            for target, (count, total) in tuple(edge.items()):
                count *= self.decay
                total *= self.decay
                if count < 0.01:
                    del edge[target]
                else:
                    edge[target] = (count, total)
            if not edge:
                stale.append(key)
        for key in stale:
            del self.edges[key]
        self.previous = list(obs)
        return prediction

    def structure(self):
        return {"units": len(self.previous or ()),
                "connections": sum(len(edge) for edge in self.edges.values()),
                "memory_bytes": 32 * len(self.edges) + 24 * sum(map(len, self.edges.values()))}
