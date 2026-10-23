"""Test whether context-addressed action uncertainty identifies a preference."""
import json
import random
import statistics
from pathlib import Path

SEEDS = range(40)
STEPS = 1000


def run(seed, reverse):
    rng = random.Random(seed)
    counts = [[0.5, 0.5] for _ in range(2)]
    choices = [0, 0]
    errors = []
    passive = []
    for _ in range(STEPS):
        context = rng.randrange(2)
        cause = rng.randrange(2)
        passive.append((context, cause))
        # Select the action with the least observed consequence evidence.
        action = min(range(2), key=lambda item: counts[item][0] + counts[item][1])
        outcome = cause ^ action ^ int(reverse)
        probability = counts[action][0] / sum(counts[action])
        errors.append((probability - outcome) ** 2)
        counts[action][outcome] += 1
        choices[action] += 1
    means = [counts[action][1] / sum(counts[action]) for action in range(2)]
    preferred = min(range(2), key=means.__getitem__)
    return {"passive": passive, "choices": choices, "means": means,
            "preferred": preferred, "mse": statistics.mean(errors)}


rows = [(run(seed, False), run(seed, True)) for seed in SEEDS]
result = {
    "seeds": len(rows),
    "steps_per_world": STEPS,
    "passive_pairs_equal": all(left["passive"] == right["passive"]
                                for left, right in rows),
    "uncertainty_policy_opposite_choices": all(
        left["choices"] != right["choices"] for left, right in rows),
    "identified_opposite_optimum": all(
        left["preferred"] != right["preferred"] for left, right in rows),
    "mean_world0_preferred": statistics.mean(left["preferred"] for left, _ in rows),
    "mean_world1_preferred": statistics.mean(right["preferred"] for _, right in rows),
    "interpretation": "passive evidence cannot set a value ordering; action-conditioned exploration alone does not define which consequence is preferable",
}
path = Path(__file__).with_name("contextual_action_identifiability_result.json")
path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
