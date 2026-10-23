"""Paired replication of action-effect closure under reversed action IDs."""
import json
import random
from pathlib import Path


class Closure:
    def __init__(self, actions=3):
        self.mean = None
        self.var = None
        self.count = [0.0] * actions
        self.last = None

    def observe(self, effect):
        if self.mean is None:
            self.mean = [[0.0] * len(effect) for _ in self.count]
            self.var = [0.0] * len(self.count)
        if self.last is None:
            return
        action = self.last
        n = self.count[action] + 1.0
        deviation = sum((x - m) ** 2 for x, m in zip(effect, self.mean[action])) / len(effect)
        self.mean[action] = [m + (x - m) / n for m, x in zip(self.mean[action], effect)]
        self.var[action] += (deviation - self.var[action]) / n
        self.count[action] = n
        self.last = None

    def act(self):
        scores = [sum(x * x for x in row) / len(row) / (self.var[a] + 0.01)
                  + 1.0 / (self.count[a] + 1.0)
                  for a, row in enumerate(self.mean)]
        self.last = max(range(len(scores)), key=scores.__getitem__)
        return self.last


def run(seed, stable, horizon=240):
    rng = random.Random(seed)
    learner = Closure()
    current = [0.0] * 12
    actions = []
    for _ in range(horizon):
        learner.observe(current)
        action = learner.act()
        if action == stable:
            current = [1.0] * 12
        elif action == (stable + 1) % 3:
            current = [rng.choice((-2.0, 2.0)) for _ in range(12)]
        else:
            current = [0.0] * 12
        actions.append(action)
    return sum(action == stable for action in actions[-120:]) / 120.0


pairs = [(run(seed, 0), run(seed, 1)) for seed in range(40)]
left = sum(pair[0] for pair in pairs) / len(pairs)
right = sum(pair[1] for pair in pairs) / len(pairs)
result = {
    "paired_worlds": len(pairs),
    "stable_action_0_share": left,
    "stable_action_1_share": right,
    "paired_min_share": sum(min(pair) for pair in pairs) / len(pairs),
    "both_worlds_ge_0_8": sum(a >= 0.8 and b >= 0.8 for a, b in pairs),
}
Path(__file__).with_name("h058_replica_result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
