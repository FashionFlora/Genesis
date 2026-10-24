from principle_organism import OrganismBrain


class System:
    def __init__(self):
        self.previous = None

    def step(self, obs):
        self.previous = list(obs)
        return [float(x) for x in obs]

    def structure(self):
        return {"units": 1, "connections": 0}
