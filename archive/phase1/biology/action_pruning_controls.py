import json
import random
from pathlib import Path


TRIALS = 40
WORLDS = 100
NEED = 0.2
EFFECT = 0.2
SD = 0.04
ACTIONS = (0, 1)


def run(seed, orientation, probe=True, prune=True):
    rng = random.Random(seed)
    effects = (-orientation * EFFECT, orientation * EFFECT)
    estimate = [0.0, 0.0]
    count = [0, 0]
    support = [1.0, 1.0]
    for t in range(TRIALS):
        action = rng.randrange(2) if probe else 0
        change = effects[action] + rng.gauss(0, SD)
        count[action] += 1
        estimate[action] += (change - estimate[action]) / count[action]
        # Local support follows whether that action's predicted outcome reduces need.
        predicted_benefit = abs(NEED) - abs(NEED + estimate[action])
        support[action] = max(0.0, support[action] + predicted_benefit)
        if prune:
            other = 1 - action
            support[other] = max(0.0, support[other] - max(0.0, predicted_benefit))
    selected = max(ACTIONS, key=lambda a: support[a]) if probe else 0
    true_best = min(ACTIONS, key=lambda a: abs(NEED + effects[a]))
    retained = [a for a in ACTIONS if support[a] > 0] if prune else list(ACTIONS)
    return selected == true_best, retained == [true_best]


def main():
    out = {}
    for label, probe, prune in (("random_intervention_local_competition", True, True),
                                ("passive_fixed_action", False, True),
                                ("random_intervention_no_pruning", True, False)):
        results = [run(seed, orientation, probe, prune)
                   for seed in range(WORLDS) for orientation in (-1, 1)]
        correct = sum(choice_ok for choice_ok, _ in results)
        exact_pruning = sum(prune_ok for _, prune_ok in results)
        out[label] = {"correct": correct, "worlds": 2 * WORLDS,
                      "accuracy": correct / (2 * WORLDS),
                      "correct_single_edge_retention": exact_pruning / (2 * WORLDS)}
    out.update({"trials_per_world": TRIALS, "world_pairs": WORLDS,
                "observation_sd": SD, "note": "toy causal-identification test"})
    path = Path(__file__).with_name("action_pruning_controls_result.json")
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
