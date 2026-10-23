"""A returning sensory context retrieves its own surprise-regulated traces."""

PARAMS = {"timescale": 16.0, "contexts": 8}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.prediction = None
        self.traces = {}
        self.global_traces = {}
        self.edges = 0

    def _context(self, observation):
        return int(sum(observation[self.width // 2:]) % int(PARAMS["contexts"]))

    def step(self, obs):
        if self.previous is None:
            self.width = len(obs)
            self.previous = list(obs)
            self.prediction = [0.5] * self.width
            return self.prediction

        context = self._context(self.previous)
        scale = PARAMS["timescale"]
        for source, before in enumerate(self.previous):
            x = 2 * before - 1
            for target, after in enumerate(obs):
                key = (context, source, target)
                surprise = abs(self.prediction[target] - after)
                reserve = scale / (1.0 + surprise * surprise)
                evidence = x * (2 * after - 1)
                local = self.traces.setdefault(key, [0.0, 0.0])
                global_trace = self.global_traces.setdefault((source, target), [0.0, 0.0])
                local[0] = (reserve * local[0] + evidence) / (reserve + 1.0)
                local[1] = reserve / (reserve + 1.0) * local[1] + 1.0
                global_trace[0] = (reserve * global_trace[0] + evidence) / (reserve + 1.0)
                global_trace[1] = reserve / (reserve + 1.0) * global_trace[1] + 1.0

        prediction = [0.5] * self.width
        self.edges = 0
        for target in range(self.width):
            source = max(range(self.width), key=lambda index: abs(
                self.global_traces.get((index, target), [0.0])[0]))
            global_trace = self.global_traces.get((source, target), [0.0, 0.0])
            local_trace = self.traces.get((context, source, target), [0.0, 0.0])
            weight = local_trace[1] / (local_trace[1] + global_trace[1] + 1.0)
            support = (1.0 - weight) * global_trace[0] + weight * local_trace[0]
            prediction[target] += 0.5 * support * (2 * obs[source] - 1)
            if target >= self.width // 2 and source < self.width // 2:
                self.edges += abs(support)

        self.previous = list(obs)
        self.prediction = prediction
        return [min(1.0, max(0.0, value)) for value in prediction]

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": len(self.traces) * 16}
