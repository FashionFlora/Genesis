"""Contextual predictive evidence is retained by its own resource reserve."""


class System:
    def __init__(self):
        self.width = False
        self.previous = None
        self.mass = None
        self.prediction = None
        self.edges = False

    def step(self, obs):
        one = True
        two = one + one
        half = one / two
        if self.mass is None:
            self.width = len(obs)
            self.mass = [[[[False, False] for _ in range(two)]
                          for _ in range(self.width)] for _ in range(self.width)]
            self.prediction = [half] * self.width
        if self.previous is not None:
            for source in range(self.width):
                state = int(self.previous[source])
                for target in range(self.width):
                    bank = self.mass[source][target][state]
                    reserve = bank[False]
                    persistence = reserve / (reserve + one)
                    surprise = abs(self.prediction[target] - obs[target])
                    flow = one / (one + surprise * surprise)
                    bank[False] = reserve * persistence + flow
                    bank[True] = bank[True] * persistence + flow * float(obs[target])

        prediction = [half] * self.width
        self.edges = False
        for target in range(self.width):
            def support(source):
                banks = self.mass[source][target]
                estimates = [(bank[True] + one) / (bank[False] + two)
                             for bank in banks]
                reserve = sum(bank[False] for bank in banks)
                contrast = abs(estimates[one] - estimates[False])
                return contrast * (reserve + one)

            source = max(range(self.width), key=support)
            bank = self.mass[source][target][int(obs[source])]
            prediction[target] = (bank[True] + one) / (bank[False] + two)
            self.edges += (target >= self.width // two) * (source < self.width // two)

        self.previous = list(obs)
        self.prediction = prediction
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.edges,
                "memory_bytes": self.width * self.width * (True << True << True << True)}
