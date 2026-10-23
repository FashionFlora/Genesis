import json
import random
from pathlib import Path


WORLD_COUNT = 40
PROBE_TRIALS = 20
NEED = 0.2
EFFECT = 0.2
OBSERVATION_SD = 0.025
ACTIONS = ("act_0", "act_1")


def simulate(seed):
    rng = random.Random(seed)
    worlds = []
    for orientation in (1, -1):
        effects = {
            "act_0": -orientation * EFFECT,
            "act_1": orientation * EFFECT,
        }
        estimates = {action: 0.0 for action in ACTIONS}
        counts = {action: 0 for action in ACTIONS}

        # Early action variability samples both interventions; internal change is the feedback.
        for trial in range(PROBE_TRIALS):
            action = ACTIONS[trial % len(ACTIONS)]
            observed_change = effects[action] + rng.gauss(0.0, OBSERVATION_SD)
            counts[action] += 1
            estimates[action] += (observed_change - estimates[action]) / counts[action]

        predicted_distance = {
            action: abs(NEED + estimates[action]) for action in ACTIONS
        }
        chosen = min(ACTIONS, key=lambda action: predicted_distance[action])
        # Only an action predicted to restore the internal variable retains support.
        support = {
            action: max(0.0, NEED - predicted_distance[action])
            for action in ACTIONS
        }
        retained = [action for action in ACTIONS if support[action] > 0.0]
        true_best = min(ACTIONS, key=lambda action: abs(NEED + effects[action]))
        worlds.append({
            "chosen_correct": chosen == true_best,
            "retained_correct": retained == [true_best],
            "passive_correct": ACTIONS[0] == true_best,
            "estimates": estimates,
        })
    return worlds


def main():
    pairs = [simulate(seed) for seed in range(WORLD_COUNT)]
    correct = sum(world["chosen_correct"] for pair in pairs for world in pair)
    structure_correct = sum(world["retained_correct"] for pair in pairs for world in pair)
    passive_correct = sum(world["passive_correct"] for pair in pairs for world in pair)
    result = {
        "world_pairs": WORLD_COUNT,
        "worlds": WORLD_COUNT * 2,
        "probe_trials_per_world": PROBE_TRIALS,
        "passive_only_accuracy": passive_correct / (WORLD_COUNT * 2),
        "intervention_choice_accuracy": correct / (WORLD_COUNT * 2),
        "correct_single_edge_retention_rate": structure_correct / (WORLD_COUNT * 2),
        "observation_sd": OBSERVATION_SD,
    }
    assert result["intervention_choice_accuracy"] > 0.95
    assert result["correct_single_edge_retention_rate"] > 0.95
    output = Path(__file__).with_name("viability_pruning_probe_result.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
