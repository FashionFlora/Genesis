import json
import random
from pathlib import Path


PAIRS = 50
NEED = 0.2
EFFECT = 0.2
PROBE_COUNTS = (4, 8, 12, 20, 40)
NOISE_LEVELS = (0.025, 0.1, 0.2, 0.4, 0.8)
ACTIONS = (0, 1)


def run_condition(probe_count, observation_sd, seed):
    rng = random.Random(seed)
    chosen_correct = 0
    retained_correct = 0
    total = 0

    for pair in range(PAIRS):
        for orientation in (-1, 1):
            effects = (-orientation * EFFECT, orientation * EFFECT)
            estimates = [0.0, 0.0]
            counts = [0, 0]

            # Motor variability supplies alternating interventions, as in the base toy.
            for trial in range(probe_count):
                action = trial % 2
                observed = effects[action] + rng.gauss(0.0, observation_sd)
                counts[action] += 1
                estimates[action] += (observed - estimates[action]) / counts[action]

            distances = [abs(NEED + estimate) for estimate in estimates]
            chosen = min(ACTIONS, key=lambda action: distances[action])
            support = [max(0.0, NEED - distance) for distance in distances]
            retained = [action for action in ACTIONS if support[action] > 0.0]
            true_best = min(
                ACTIONS,
                key=lambda action: abs(NEED + effects[action]),
            )
            chosen_correct += chosen == true_best
            retained_correct += retained == [true_best]
            total += 1

    return {
        "probe_trials_per_world": probe_count,
        "observation_sd": observation_sd,
        "worlds": total,
        "choice_accuracy": chosen_correct / total,
        "single_edge_retention_accuracy": retained_correct / total,
    }


def main():
    conditions = []
    for noise_index, observation_sd in enumerate(NOISE_LEVELS):
        for probe_count in PROBE_COUNTS:
            seed = 1000 + noise_index * 100 + probe_count
            conditions.append(run_condition(probe_count, observation_sd, seed))

    result = {
        "world_pairs_per_condition": PAIRS,
        "need": NEED,
        "action_effect_magnitude": EFFECT,
        "conditions": conditions,
        "limitation": "The alternating intervention schedule and viability target are supplied.",
    }
    output = Path(__file__).with_name("need_probe_noise_sweep_result.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
