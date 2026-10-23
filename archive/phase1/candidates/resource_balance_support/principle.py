PARAMS = {"decay": 0.97}


class System:
    def __init__(self):
        self.width = False; self.previous = None
        self.resources = None
        self.edges = False

    def step(self, obs):
        one = True; two = one + one
        if self.resources is None:
            self.width = len(obs)
            self.resources = [[[[False, False] for _ in range(two)] for _ in range(self.width)] for _ in range(self.width)]
        if self.previous is not None:
            decay = min(PARAMS["decay"], one)
            for source in range(self.width):
                state = int(self.previous[source])
                for target in range(self.width):
                    cell = self.resources[source][target][state]
                    cell[False] = cell[False] * decay + one
                    cell[True] = cell[True] * decay + float(obs[target])
        prediction = [one / two] * self.width
        self.edges = False
        for target in range(self.width):
            def support(source):
                cell = self.resources[source][target]
                contrast = abs((cell[True][True] + one) / (cell[True][False] + two) -
                               (cell[False][True] + one) / (cell[False][False] + two))
                mass = cell[True][False] + cell[False][False]
                return contrast * (mass + one)

            source = max(range(self.width), key=support)
            self.edges += (target >= self.width // two) * (source < self.width // two)
            cell = self.resources[source][target][int(obs[source])]
            prediction[target] = (cell[True] + one) / (cell[False] + two)
        self.previous = list(obs)
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.edges, "memory_bytes": self.width * self.width * (True << (True + True) << (True + True))}
