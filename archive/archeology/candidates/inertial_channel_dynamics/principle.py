"""Local prediction error changes the inertia of each observed degree of freedom."""

PARAMS = {"adaptation": 0.2}


class System:
    def __init__(self):
        self.previous = None
        self.velocity = None
        self.inertia = None
        self.pending_delta = None
        self.edges = 0.0

    def step(self, obs):
        if self.previous is None:
            self.previous = list(obs)
            self.inertia = [0.0] * len(obs)
            self.velocity = [0.0] * len(obs)
            self.pending_delta = [0.0] * len(obs)
            self.pending_prediction = [0.5] * len(obs)
            return [0.5] * len(obs)

        rate = PARAMS["adaptation"]
        for i, value in enumerate(obs):
            error = value - self.pending_prediction[i]
            delta = self.pending_delta[i]
            self.inertia[i] = max(-1.0, min(1.0, self.inertia[i] + rate * error * delta))

        prediction = []
        for i, value in enumerate(obs):
            delta = value - self.previous[i]
            self.pending_delta[i] = delta
            prediction.append(max(0.0, min(1.0, value + self.inertia[i] * delta)))
        self.pending_prediction = prediction
        self.previous = list(obs)
        self.edges = sum(abs(value) for value in self.inertia)
        return prediction

    def structure(self):
        return {"units": len(self.previous or []), "connections": self.edges,
                "memory_bytes": len(self.inertia or []) * 16}
