"""Paired action worlds: passive histories match, causal option effects reverse."""
import json
import random
from pathlib import Path


def run(seed, preferred):
    rng = random.Random(seed)
    estimate = [0.0, 0.0]
    count = [0, 0]
    chosen = []
    for turn in range(160):
        action = turn if turn < 2 else max(
            range(2), key=lambda a: estimate[a] + 1.0 / (count[a] + 1.0))
        change = (0.65 if action == preferred else -0.65) + rng.gauss(0.0, 0.08)
        count[action] += 1
        estimate[action] += (change - estimate[action]) / count[action]
        chosen.append(action)
    return sum(action == preferred for action in chosen[-80:]) / 80.0


scores = [run(seed, seed % 2) for seed in range(40)]
result = {"paired_worlds": len(scores), "late_best_action_share": sum(scores) / len(scores)}
Path(__file__).with_name("option_delta_test_result.json").write_text(
    json.dumps(result, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
