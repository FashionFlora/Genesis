"""Reference: predict the uninformative Bernoulli mean on every channel."""


class System:
    def step(self, obs):
        return [0.5 for _ in obs]

    def structure(self):
        return {"units": 0, "connections": 0, "memory_bytes": 0}
