"""Test whether repeatable action-conditioned sensory return guides action."""

import json
import random
from pathlib import Path


def run(seed, noise, policy, horizon=80):
    rng = random.Random(seed)
    target = rng.randrange(2)
    pattern = [rng.choice((-1.0, 1.0)) for _ in range(8)]
    means = [[0.0] * 8 for _ in range(3)]
    counts = [0, 0, 0]
    chosen = []
    for t in range(horizon):
        if t < 3:
            action = t
        elif policy == "reliable_return":
            action = max(range(3), key=lambda a: sum(x * x for x in means[a]))
        else:
            action = rng.randrange(3)
        if action == target:
            delta = [x + rng.gauss(0.0, noise) for x in pattern]
        elif action == 1 - target:
            delta = [rng.choice((-1.0, 1.0)) + rng.gauss(0.0, noise)
                     for _ in pattern]
        else:
            delta = [rng.gauss(0.0, noise) for _ in pattern]
        counts[action] += 1
        rate = 1.0 / counts[action]
        means[action] = [old + rate * (new - old)
                         for old, new in zip(means[action], delta)]
        chosen.append(action)
    return sum(action == target for action in chosen[-40:]) / 40.0


out = {"worlds": 400, "horizon": 80, "metric": "late target-action choice share",
       "results": {}}
for noise in (0.0, 0.35, 0.8):
    results = {name: [] for name in ("reliable_return", "matched_random")}
    for seed in range(out["worlds"]):
        for policy in results:
            results[policy].append(run(seed, noise, policy))
    out["results"][str(noise)] = {
        policy: sum(values) / len(values) for policy, values in results.items()
    }
    out["results"][str(noise)]["advantage"] = (
        out["results"][str(noise)]["reliable_return"] -
        out["results"][str(noise)]["matched_random"])

path = Path(__file__).with_name("sensory_return_test_result.json")
path.write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out["results"], sort_keys=True))
