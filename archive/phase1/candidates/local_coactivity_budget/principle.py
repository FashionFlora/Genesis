"""A locally capped coactivity mass is edge, forecast, and persistence."""

PARAMS = {"budget": 1.0, "learning_rate": 0.1}


def project_budget(values, budget):
    ordered = sorted(values, reverse=True)
    total = 0.0
    threshold = 0.0
    for index, value in enumerate(ordered, 1):
        total += value
        candidate = (total - budget) / index
        if index == len(ordered) or ordered[index] <= candidate:
            threshold = candidate
            break
    return [max(0.0, value - threshold) for value in values]


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.mass = None
        self.edges = 0

    def step(self, observation):
        if self.mass is None:
            self.width = len(observation)
            self.mass = [[0.0] * self.width for _ in range(self.width)]

        if self.previous is not None:
            rate = PARAMS["learning_rate"]
            budget = PARAMS["budget"]
            for source, before in enumerate(self.previous):
                coactive = [before * after for after in observation]
                mean = sum(coactive) / self.width
                updated = [
                    self.mass[source][target] + rate * (coactive[target] - mean)
                    for target in range(self.width)
                ]
                self.mass[source] = project_budget(updated, budget)

        prediction = [0.5] * self.width
        for target in range(self.width):
            total = sum(self.mass[source][target] for source in range(self.width))
            if total:
                signed = sum(
                    self.mass[source][target] * (2.0 * observation[source] - 1.0)
                    for source in range(self.width)
                )
                prediction[target] += 0.5 * signed / total

        self.edges = sum(value > 0.0 for row in self.mass for value in row)
        self.previous = list(observation)
        return [min(1.0, max(0.0, value)) for value in prediction]

    def structure(self):
        return {
            "units": self.width,
            "connections": self.edges,
            "memory_bytes": self.width * self.width * 8,
        }
