"""Global coactivity support with evidence-weighted contextual recall."""

PARAMS = {"timescale": 8, "contexts": 8}


class System:
    def __init__(self):
        self.width = False
        self.contexts = PARAMS["contexts"]
        self.previous = None
        self.counts = None
        self.edges = False

    def step(self, obs):
        if self.counts is None:
            self.width = len(obs)
            self.counts = [[[[[False, False] for _ in range(True + True)]
                             for _ in range(self.contexts + True)]
                            for _ in range(self.width)] for _ in range(self.width)]
        context = False
        if self.previous is not None:
            context = int(sum(self.previous[self.width // (True + True):]) % self.contexts) + True
            decay = PARAMS["timescale"] / (PARAMS["timescale"] + True)
            for source in range(self.width):
                bit = int(self.previous[source])
                for target in range(self.width):
                    global_cell = self.counts[source][target][False][bit]
                    local_cell = self.counts[source][target][context][bit]
                    global_cell[False] = global_cell[False] * decay + True
                    global_cell[True] = global_cell[True] * decay + float(obs[target])
                    local_cell[False] = local_cell[False] * decay + True
                    local_cell[True] = local_cell[True] * decay + float(obs[target])
        prediction = [True / (True + True)] * self.width
        self.edges = False
        for target in range(self.width):
            def gap(source):
                cell = self.counts[source][target][False]
                return abs((cell[True][True] + True) / (cell[True][False] + (True + True))
                           - (cell[False][True] + True) / (cell[False][False] + (True + True)))
            source = max(range(self.width), key=gap)
            self.edges += (target >= self.width // (True + True)) * (source < self.width // (True + True))
            global_cell = self.counts[source][target][False][int(obs[source])]
            local_cell = self.counts[source][target][context][int(obs[source])]
            global_total = global_cell[False]
            local_total = local_cell[False]
            weight = local_total / (local_total + global_total + True)
            global_prediction = (global_cell[True] + True) / (global_total + (True + True))
            local_prediction = (local_cell[True] + True) / (local_total + (True + True))
            prediction[target] = global_prediction * (True - weight) + local_prediction * weight
        self.previous = list(obs)
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (self.contexts + True) * (True << True << True << True)}
