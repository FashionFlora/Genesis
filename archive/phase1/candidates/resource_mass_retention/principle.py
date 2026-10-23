class System:
    def __init__(self):
        self.width = False
        self.previous = None
        self.mass = None
        self.edges = False

    def step(self, obs):
        one = True
        two = one + one
        if self.mass is None:
            self.width = len(obs)
            self.mass = [[[[False, False] for _ in range(two)]
                          for _ in range(self.width)] for _ in range(self.width)]
        if self.previous is not None:
            for source in range(self.width):
                state = int(self.previous[source])
                for target in range(self.width):
                    bank = self.mass[source][target][state]
                    reserve = bank[False] + bank[True]
                    persistence = reserve / (reserve + one)
                    bank[False] *= persistence
                    bank[True] *= persistence
                    bank[False] += one
                    bank[True] += float(obs[target])
        prediction = [one / two] * self.width
        self.edges = False
        for target in range(self.width):
            def support(source):
                cell = self.mass[source][target]
                gap = abs((cell[True][True] + one) / (cell[True][False] + two)
                          - (cell[False][True] + one) / (cell[False][False] + two))
                reserve = cell[True][False] + cell[False][False]
                return gap * (reserve + one)

            source = max(range(self.width), key=support)
            self.edges += (target >= self.width // two) * (source < self.width // two)
            cell = self.mass[source][target][int(obs[source])]
            prediction[target] = (cell[True] + one) / (cell[False] + two)
        self.previous = list(obs)
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (True << True << True << True)}
