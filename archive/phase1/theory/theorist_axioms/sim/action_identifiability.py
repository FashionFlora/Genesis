"""Check whether passive prediction identifies a useful intervention."""
import json
import random
import statistics
from pathlib import Path

SEEDS = range(40)
STEPS = 1000


def run(seed, reverse):
    rng = random.Random(seed)
    passive_left = []
    passive_right = []
    action_outcomes = [[], []]
    for _ in range(STEPS):
        cause = rng.randrange(2)
        passive_left.append(cause)
        passive_right.append(cause)
        for action in range(2):
            outcome = cause ^ action ^ int(reverse)
            action_outcomes[action].append(outcome)
    return {
        "passive_mean": statistics.mean(passive_left),
        "passive_pair_equal": passive_left == passive_right,
        "action_means": [statistics.mean(values) for values in action_outcomes],
        "best_action": min(range(2), key=lambda action: statistics.mean(action_outcomes[action])),
    }


rows = [(run(seed, False), run(seed, True)) for seed in SEEDS]
result = {
    "seeds": len(rows),
    "steps_per_seed": STEPS,
    "passive_pairs_equal": all(a["passive_pair_equal"] for a, _ in rows),
    "mean_abs_passive_difference": statistics.mean(
        abs(a["passive_mean"] - b["passive_mean"]) for a, b in rows),
    "worlds_choose_opposite_actions": all(a["best_action"] != b["best_action"] for a, b in rows),
    "world_0_best_action_fraction": statistics.mean(a["best_action"] for a, _ in rows),
    "world_1_best_action_fraction": statistics.mean(b["best_action"] for _, b in rows),
    "interpretation": "passive observations alone do not identify an action preference",
}
out = Path(__file__).with_name("action_identifiability_result.json")
out.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
