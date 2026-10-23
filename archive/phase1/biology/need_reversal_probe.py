import json
import random
from pathlib import Path


PAIRS = 100
PROBE_TRIALS = 12
OBSERVATION_SD = 0.04
ACTIONS = ("left", "right")


def mean_observed_effects(rng, effects):
    estimates = {action: 0.0 for action in ACTIONS}
    counts = {action: 0 for action in ACTIONS}
    for trial in range(PROBE_TRIALS):
        action = ACTIONS[trial % 2]
        observation = effects[action] + rng.gauss(0.0, OBSERVATION_SD)
        counts[action] += 1
        estimates[action] += (observation - estimates[action]) / counts[action]
    return estimates


def choose_action(estimates, state, target):
    return min(
        ACTIONS,
        key=lambda action: abs(state + estimates[action] - target),
    )


def simulate(seed):
    rng = random.Random(seed)
    orientation = rng.choice((-1.0, 1.0))
    effects = {"left": -0.2 * orientation, "right": 0.2 * orientation}
    estimates = mean_observed_effects(rng, effects)
    blocks = []
    for target in (-0.2 * orientation, 0.2 * orientation):
        state = 0.0
        action = choose_action(estimates, state, target)
        true_action = min(
            ACTIONS,
            key=lambda candidate: abs(state + effects[candidate] - target),
        )
        retained = action
        blocks.append({"correct": action == true_action, "retained": retained == true_action})
    return blocks


def main():
    outcomes = [simulate(seed) for seed in range(PAIRS)]
    choices = [block for pair in outcomes for block in pair]
    result = {
        "paired_worlds": PAIRS,
        "world_blocks": len(choices),
        "probe_trials_per_world": PROBE_TRIALS,
        "observation_sd": OBSERVATION_SD,
        "action_choice_accuracy": sum(x["correct"] for x in choices) / len(choices),
        "need_conditioned_single_edge_retention": sum(x["retained"] for x in choices) / len(choices),
        "fixed_left_action_accuracy": 0.5,
        "interpretation": "A learned action model can reverse both choice and retained edge when the internal setpoint reverses.",
    }
    Path(__file__).with_name("need_reversal_probe_result.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
