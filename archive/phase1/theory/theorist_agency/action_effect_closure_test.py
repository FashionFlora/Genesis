"""Toy test for one law: choose actions by retained causal effect."""
import json
import random
from pathlib import Path


class Closure:
    def __init__(self, actions=3):
        self.actions = actions
        self.mean = None
        self.var = None
        self.count = [0.0] * actions
        self.last = None

    def observe(self, effect):
        if self.mean is None:
            self.mean = [[0.0] * len(effect) for _ in range(self.actions)]
            self.var = [0.0] * self.actions
        if self.last is not None:
            a, old = self.last
            n = self.count[a] + 1.0
            delta = sum((x - y) ** 2 for x, y in zip(effect, self.mean[a])) / len(effect)
            rate = 1.0 / n
            self.mean[a] = [m + rate * (x - m) for m, x in zip(self.mean[a], effect)]
            self.var[a] += rate * (delta - self.var[a])
            self.count[a] = n
            self.last = None

    def act(self):
        scores = []
        for a in range(self.actions):
            signal = sum(x * x for x in self.mean[a]) / len(self.mean[a])
            scores.append(signal / (self.var[a] + 0.01) + 1.0 / (self.count[a] + 1.0))
        choice = max(range(self.actions), key=scores.__getitem__)
        self.last = (choice, None)
        return choice


def run(seed, horizon=240):
    rng = random.Random(seed)
    stable = seed % 2
    learner = Closure()
    action_log = []
    previous = [0.0] * 12
    for step in range(horizon):
        effect = [0.0] * 12 if step == 0 else current
        learner.observe(effect)
        action = learner.act()
        if action == stable:
            current = [1.0] * 12
        elif action == (stable + 1) % 3:
            current = [rng.choice((-2.0, 2.0)) for _ in range(12)]
        else:
            current = [0.0] * 12
        action_log.append(action)
    return stable, sum(a == stable for a in action_log[-120:]) / 120.0


rows = [run(seed) for seed in range(40)]
out = {"paired_worlds": len(rows), "late_best_action_share": sum(v for _, v in rows) / len(rows),
       "world0_share": rows[0][1], "world1_share": rows[1][1]}
Path(__file__).with_name("action_effect_closure_test_result.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, sort_keys=True))
