"""Small stream-track counterpart for the pixel-local eligibility principle."""

import math
import random


class System:
    def __init__(self):
        self.decay = 0.985
        self.previous = None
        self.links = {}

    def step(self, obs):
        values = list(obs)
        if self.previous is not None:
            for source, value in enumerate(self.previous):
                key = (source, int(value))
                edge = self.links.setdefault(key, {})
                for target, result in enumerate(values):
                    strength, total = edge.get(target, (0.0, 0.0))
                    edge[target] = (strength * self.decay + 1.0,
                                    total * self.decay + float(result))
        prediction = []
        for target in range(len(values)):
            estimates = [self.links.get((source, int(value)), {}).get(target, (0.0, 0.5))[1]
                         / max(self.links.get((source, int(value)), {}).get(target, (0.0, 0.5))[0], 1.0)
                         for source, value in enumerate(values)]
            prediction.append(sum(estimates) / max(len(estimates), 1))
        for key in list(self.links):
            edge = self.links[key]
            for target, (strength, total) in list(edge.items()):
                strength *= self.decay
                total *= self.decay
                if strength < 0.01:
                    del edge[target]
                else:
                    edge[target] = (strength, total)
            if not edge:
                del self.links[key]
        self.previous = values
        return prediction

    def structure(self):
        return {"units": len(self.previous or ()),
                "connections": sum(len(edge) for edge in self.links.values()),
                "memory_bytes": 32 * len(self.links) + 24 * sum(map(len, self.links.values()))}


def _perturb_params(params, seed):
    rng = random.Random(seed)
    return {key: value * math.exp(rng.uniform(math.log(0.5), math.log(2.0)))
            for key, value in params.items()}
