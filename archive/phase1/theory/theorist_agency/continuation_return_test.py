"""Toy: action is ordered only by the observed continuation it causes."""
import json
import random
from pathlib import Path


def run(seed, horizon=160):
    rng = random.Random(seed)
    estimate = [0.0, 0.0]
    count = [0, 0]
    chosen = []
    for t in range(horizon):
        action = t if t < 2 else max(range(2), key=lambda a:
                                      estimate[a] + 1.0 / (count[a] + 1.0))
        continuation = (0.85 if action == 1 else 0.2) + rng.gauss(0.0, 0.08)
        count[action] += 1
        estimate[action] += (continuation - estimate[action]) / count[action]
        chosen.append(action)
    return sum(a == 1 for a in chosen[-80:]) / 80.0


scores = [run(seed) for seed in range(40)]
out = {"worlds": len(scores), "late_best_action_share": sum(scores) / len(scores)}
Path(__file__).with_name("continuation_return_test_result.json").write_text(
    json.dumps(out, indent=2) + "\n")
print(json.dumps(out, sort_keys=True))
