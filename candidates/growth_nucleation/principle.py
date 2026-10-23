"""Sparse predictive links nucleated by unexplained target transitions."""

PARAMS = {"decay": 0.992, "support": 12.0, "prune": 0.035}
ZERO = False
ONE = True
TWO = ONE + ONE


class System:
    def __init__(self):
        self.previous = None
        self.targets = {}
        self.edges = {}
        self.decay = PARAMS["decay"]

    def _probability(self, source, target, value):
        edge = self.edges[(source, target)]
        counts = edge[0] if value else edge[1]
        return (counts[ONE] + ONE) / (counts[ZERO] + TWO)

    def step(self, obs):
        prediction = []
        if self.previous is None:
            prediction = [0.5 for _ in obs]
        else:
            for target, value in enumerate(obs):
                base = self.targets.get(target, [ZERO, ZERO])
                p = (base[ONE] + ONE) / (base[ZERO] + TWO)
                choices = []
                for source in range(len(obs)):
                    edge = self.edges.get((source, target))
                    if edge is None:
                        continue
                    zero, one, age, utility = edge
                    n0, s0 = zero
                    n1, s1 = one
                    p0 = (s0 + ONE) / (n0 + TWO)
                    p1 = (s1 + ONE) / (n1 + TWO)
                    confidence = min(1.0, (n0 + n1) / PARAMS["support"])
                    strength = confidence * utility
                    choices.append((strength, p0 if self.previous[source] < 0.5 else p1))
                if choices:
                    strength, linked = max(choices)
                    p = p * (ONE - strength) + linked * strength
                prediction.append(p)

            errors = []
            for target, value in enumerate(obs):
                base = self.targets.setdefault(target, [ZERO, ZERO])
                p = (base[ONE] + ONE) / (base[ZERO] + TWO)
                errors.append((value - p) ** 2)

            for key, edge in list(self.edges.items()):
                source, target = key
                zero, one, age, utility = edge
                sample = one if self.previous[source] >= 0.5 else zero
                sample[ZERO] = sample[ZERO] * self.decay + ONE
                sample[ONE] = sample[ONE] * self.decay + obs[target]
                edge[2] = age * self.decay + ONE
                n0, s0 = zero
                n1, s1 = one
                association = abs((s1 + ONE) / (n1 + TWO) -
                                  (s0 + ONE) / (n0 + TWO))
                edge[3] = edge[3] * self.decay + (ONE - self.decay) * association

            for target, error in enumerate(errors):
                if error <= 0.12:
                    continue
                for source in range(len(obs)):
                    key = (source, target)
                    if source != target and key not in self.edges:
                        self.edges[key] = [[0.0, 0.0], [0.0, 0.0], 0.0, 0.0]

            for target, value in enumerate(obs):
                base = self.targets[target]
                base[ZERO] = base[ZERO] * self.decay + ONE
                base[ONE] = base[ONE] * self.decay + value

            for key, edge in list(self.edges.items()):
                if edge[2] > PARAMS["support"] and edge[3] < PARAMS["prune"]:
                    del self.edges[key]

        self.previous = list(obs)
        return prediction

    def structure(self):
        endpoints = set()
        for source, target in self.edges:
            endpoints.add(source)
            endpoints.add(target)
        return {"units": 1 + len(endpoints), "connections": len(self.edges),
                "memory_bytes": 64 + 64 * len(self.edges) + 24 * len(self.targets)}
