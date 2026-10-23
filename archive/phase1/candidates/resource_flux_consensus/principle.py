"""Prediction is the consensus of relations weighted by retained resource."""


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
            winner = None
            for source in range(self.width):
                cell = self.mass[source][target]
                contrast = abs((cell[True][True] + one) / (cell[True][False] + two)
                               - (cell[False][True] + one) / (cell[False][False] + two))
                reserve = sum(bank[False] + bank[True] for bank in cell)
                weight = contrast * reserve
                state = int(obs[source])
                estimate = (cell[state][True] + one) / (cell[state][False] + two)
                candidate = (weight, estimate, source)
                if winner is None or candidate[0] > winner[0]:
                    winner = candidate
            if winner is not None:
                prediction[target] = winner[1]
            if target >= self.width // two:
                self.edges += winner[0] if winner is not None else False
        self.previous = list(obs)
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (True << True << True << True)}
