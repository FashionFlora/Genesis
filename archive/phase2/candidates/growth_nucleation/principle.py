"""Predictive links compete for a finite budget of explanatory credit."""

PARAMS = {"decay": 0.97, "budget_ratio": 2.0, "window": 12.0,
          "surprise": 0.09, "birth_credit": 0.22, "floor": 0.018}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.targets = []
        self.edges = {}
        self.history = []
        self.budget = 0

    def _probability(self, edge, bit):
        counts = edge[0] if bit < 0.5 else edge[1]
        return (counts[1] + 1.0) / (counts[0] + 2.0)

    def _birth(self, target):
        if len(self.history) < 2:
            return
        best_source = None
        best_score = 0.0
        for source in range(self.width):
            if source == target:
                continue
            pairs = [(row[source], row[target]) for row in self.history]
            agreement = sum(1.0 for a, b in pairs if a == b) / len(pairs)
            score = abs(agreement - 0.5)
            if score > best_score:
                best_source, best_score = source, score
        if best_source is None:
            return
        key = (best_source, target)
        if key not in self.edges:
            self.edges[key] = [[0.0, 0.0], [0.0, 0.0], PARAMS["birth_credit"], 0.0]

    def _evict(self):
        while len(self.edges) > self.budget:
            key = min(self.edges, key=lambda item: self.edges[item][2])
            del self.edges[key]

    def step(self, obs):
        if not self.targets:
            self.width = len(obs)
            self.targets = [[0.0, 0.0] for _ in obs]
            self.budget = max(1, int(self.width * PARAMS["budget_ratio"]))
        prediction = []
        selected = {}
        for target, value in enumerate(obs):
            base = self.targets[target]
            p = (base[1] + 1.0) / (base[0] + base[1] + 2.0)
            choices = [(edge[2], key, edge) for key, edge in self.edges.items()
                       if key[1] == target]
            if choices:
                _, key, edge = max(choices)
                p = self._probability(edge, self.previous[key[0]])
                selected[target] = (key, p)
            prediction.append(p)
        if self.previous is not None:
            for target, value in enumerate(obs):
                base = self.targets[target]
                old = (base[1] + 1.0) / (base[0] + base[1] + 2.0)
                if (value - old) ** 2 > PARAMS["surprise"]:
                    self._birth(target)
            for target, (key, predicted) in selected.items():
                edge = self.edges.get(key)
                if edge is None:
                    continue
                reward = max(0.0, 0.5 - (obs[target] - predicted) ** 2)
                edge[2] = PARAMS["decay"] * edge[2] + (1.0 - PARAMS["decay"]) * reward
                edge[3] = edge[3] * PARAMS["decay"] + 1.0
            for key, edge in list(self.edges.items()):
                source, target = key
                counts = edge[0] if self.previous[source] < 0.5 else edge[1]
                counts[0] = counts[0] * PARAMS["decay"] + 1.0
                counts[1] = counts[1] * PARAMS["decay"] + obs[target]
                if edge[3] > PARAMS["window"] and edge[2] < PARAMS["floor"]:
                    del self.edges[key]
            self._evict()
            for target, value in enumerate(obs):
                base = self.targets[target]
                base[0] = base[0] * PARAMS["decay"] + 1.0
                base[1] = base[1] * PARAMS["decay"] + value
        self.previous = list(obs)
        self.history.append(self.previous)
        if len(self.history) > int(PARAMS["window"]):
            self.history.pop(0)
        return prediction

    def structure(self):
        endpoints = {item for key in self.edges for item in key}
        return {"units": 1 + len(endpoints), "connections": len(self.edges),
                "memory_bytes": 64 + 72 * len(self.edges) + 16 * self.width * len(self.history)}
