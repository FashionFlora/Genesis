"""Probe when endogenous viability feedback can identify a useful action edge."""
import json
import random
from pathlib import Path


WORLDS = 200
PROBE_COUNTS = (1, 2, 4, 8, 16)
NEED = 0.2
EFFECT = 0.2
OBSERVATION_SD = 0.08
ACTIONS = ("act_0", "act_1")


def run_world(seed, probes):
    rng = random.Random(seed)
    orientation = 1 if seed % 2 == 0 else -1
    effects = {"act_0": -orientation * EFFECT, "act_1": orientation * EFFECT}
    estimates = {action: 0.0 for action in ACTIONS}
    counts = {action: 0 for action in ACTIONS}
    for trial in range(probes):
        action = ACTIONS[trial % len(ACTIONS)]
        change = effects[action] + rng.gauss(0.0, OBSERVATION_SD)
        counts[action] += 1
        estimates[action] += (change - estimates[action]) / counts[action]
    predicted_distance = {a: abs(NEED + estimates[a]) for a in ACTIONS}
    chosen = min(ACTIONS, key=lambda a: predicted_distance[a])
    # Local support persists only when the action's predicted consequence reduces need.
    support = {a: max(0.0, NEED - predicted_distance[a]) for a in ACTIONS}
    retained = [a for a in ACTIONS if support[a] > 0.0]
    true_best = min(ACTIONS, key=lambda a: abs(NEED + effects[a]))
    return chosen == true_best, retained == [true_best]


def main():
    rows = []
    for probes in PROBE_COUNTS:
        outcomes = [run_world(seed, probes) for seed in range(WORLDS)]
        rows.append({
            "probe_trials": probes,
            "worlds": WORLDS,
            "action_accuracy": sum(x[0] for x in outcomes) / WORLDS,
            "correct_single_edge_rate": sum(x[1] for x in outcomes) / WORLDS,
        })
    result = {
        "worlds": WORLDS,
        "need_magnitude": NEED,
        "action_effect_magnitude": EFFECT,
        "observation_sd": OBSERVATION_SD,
        "results": rows,
        "limitation": "Supplied binary actions and target; no organismal resource dynamics or neuron growth.",
    }
    out = Path(__file__).with_name("viability_intervention_boundary_result.json")
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
