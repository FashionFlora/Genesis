"""Paired test of whether learned action consequences control later choice."""
import json
import random
from pathlib import Path


def run(seed, preferred, mode, horizon=160):
    rng = random.Random(seed)
    estimates = [0.0, 0.0]
    counts = [0, 0]
    choices = []
    for turn in range(horizon):
        if turn < 2:
            action = turn
        elif mode == "learned":
            action = max(range(2), key=lambda a: estimates[a] + 1.0 / (counts[a] + 1.0))
        elif mode == "frozen":
            action = max(range(2), key=lambda a: 1.0 / (counts[a] + 1.0))
        else:
            action = max(range(2), key=lambda a:
                         rng.gauss(0.0, 0.65) + 1.0 / (counts[a] + 1.0))
        outcome = (0.65 if action == preferred else -0.65) + rng.gauss(0.0, 0.08)
        counts[action] += 1
        estimates[action] += (outcome - estimates[action]) / counts[action]
        choices.append(action)
    return sum(a == preferred for a in choices[-80:]) / 80.0


rows = {mode: [run(seed, seed % 2, mode) for seed in range(40)]
        for mode in ("learned", "frozen", "random")}
result = {"paired_worlds": 40,
          "late_preferred_action_share": {mode: sum(scores) / len(scores)
                                           for mode, scores in rows.items()},
          "learned_minus_frozen": sum(rows["learned"]) / 40 - sum(rows["frozen"]) / 40,
          "learned_minus_random": sum(rows["learned"]) / 40 - sum(rows["random"]) / 40}
Path(__file__).with_name("return_ablation_test_result.json").write_text(
    json.dumps(result, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
