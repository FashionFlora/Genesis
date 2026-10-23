"""Check whether context-conditioned sensory return tracks a changing action."""

import json
import random
from pathlib import Path


def run(seed, policy, worlds=200):
    rng = random.Random(seed)
    counts = [[0.0] * 3 for _ in range(2)]
    means = [[[0.0] * 8 for _ in range(3)] for _ in range(2)]
    energy = [[0.0] * 3 for _ in range(2)]
    correct = []
    for t in range(worlds):
        context = (t // 25) % 2
        target = context
        if t < 6 or policy == "random":
            action = t % 3 if t < 6 else rng.randrange(3)
        else:
            scores = [sum(x * x for x in means[context][a]) /
                      max(energy[context][a], 1 / 8) ** .5 for a in range(3)]
            action = max(range(3), key=scores.__getitem__)
        if action == target:
            delta = [1.0] * 8
        elif action == 1 - target:
            delta = [rng.choice((-1.0, 1.0)) for _ in range(8)]
        else:
            delta = [0.0] * 8
        n = counts[context][action] + 1
        rate = 1 / n
        means[context][action] = [m + rate * (d - m)
                                   for m, d in zip(means[context][action], delta)]
        energy[context][action] += rate * (sum(d*d for d in delta) - energy[context][action])
        counts[context][action] = n
        correct.append(action == target)
    return sum(correct[-100:]) / 100


scores = {policy: sum(run(seed, policy) for seed in range(100)) / 100
          for policy in ("conditioned", "random")}
out = {"worlds": 100, "horizon": 200, "late_correct_action_share": scores,
       "gain": scores["conditioned"] - scores["random"]}
Path(__file__).with_name("contextual_return_test_result.json").write_text(
    json.dumps(out, indent=2) + "\n")
print(json.dumps(out, sort_keys=True))
