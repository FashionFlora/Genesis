"""Local phase locking stores a binary relation as oscillator phase."""
import math

PARAMS = {"gain": 0.12, "damping": 0.04}


class System:
    def __init__(self):
        self.previous = None
        self.width = 0
        self.phase = None
        self.gain = PARAMS["gain"]
        self.damping = PARAMS["damping"]

    def step(self, obs):
        if self.phase is None:
            self.width = len(obs)
            self.phase = [[1.5707963267948966 for _ in obs] for _ in obs]
        if self.previous is not None:
            for source, before in enumerate(self.previous):
                x = 2.0 * before - 1.0
                for target, after in enumerate(obs):
                    signed_relation = x * (2.0 * after - 1.0)
                    angle = self.phase[source][target]
                    self.phase[source][target] = angle + (
                        -self.gain * signed_relation + self.damping * math.cos(angle)
                    ) * math.sin(angle)
        prediction = [0.5] * self.width
        for target in range(self.width):
            source = max(range(self.width), key=lambda i: abs(math.cos(self.phase[i][target])))
            strength = math.cos(self.phase[source][target])
            prediction[target] = 0.5 + 0.5 * strength * (2.0 * obs[source] - 1.0)
        self.previous = [float(value) for value in obs]
        return prediction

    def structure(self):
        return {"units": self.width, "connections": self.width * self.width,
                "memory_bytes": self.width * self.width * 8}
