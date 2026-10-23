"""Toy boundary test for viability-driven, action-conditioned structural change.

The organism receives no external reward.  It estimates each action's effect from
an efference-copy label plus noisy interoceptive feedback, samples uncertain actions,
and gives local structural support to actions that reduce current viability error.
"""

import json
import math
import random
from pathlib import Path


WORLDS = 200
STEPS = 200
SWITCH = STEPS // 2
TARGET_MAGNITUDE = 0.2
OBS_SD = 0.08
ACTION_COST = 1.0
EDGE_THRESHOLD = 0.35
SUPPORT_DECAY = 0.08


def softmax_pick(scores, temperature, rng):
    weights = [math.exp(-(s - min(scores)) / max(temperature, 1e-6)) for s in scores]
    total = sum(weights)
    draw = rng.random() * total
    for i, weight in enumerate(weights):
        draw -= weight
        if draw <= 0:
            return i
    return len(scores) - 1


def run(seed, mode):
    rng = random.Random(seed)
    orientation = rng.choice((-1.0, 1.0))
    initial_target_sign = rng.choice((-1.0, 1.0))
    effects = (-orientation * TARGET_MAGNITUDE, orientation * TARGET_MAGNITUDE)
    estimate = [0.0, 0.0]
    count = [0, 0]
    support = [0.5, 0.5]
    energy = float(STEPS)
    records = []
    for step in range(STEPS):
        target_sign = initial_target_sign if step < SWITCH else -initial_target_sign
        target = target_sign * TARGET_MAGNITUDE
        need = abs(target)
        predicted_error = [abs(target - estimate[a]) for a in range(2)]
        uncertainty = [1.0 / math.sqrt(count[a] + 1.0) for a in range(2)]
        if mode == "endogenous_uncertainty":
            # The same viability error that selects an action controls how much
            # model uncertainty is tolerated; no external reward is supplied.
            scores = [predicted_error[a] for a in range(2)]
            temperature = 0.015 + 0.20 * need * (uncertainty[0] + uncertainty[1])
            action = softmax_pick(scores, temperature, rng)
        elif mode == "greedy_predictive":
            action = min(range(2), key=lambda a: predicted_error[a])
        else:
            action = 0

        observed = effects[action] + rng.gauss(0.0, OBS_SD)
        prior_error = abs(target - 0.0)
        post_error = abs(target - observed)
        benefit = prior_error - post_error
        count[action] += 1
        estimate[action] += (observed - estimate[action]) / count[action]

        # Local support is a persistence trace: useful active edges gain it,
        # while all edges pay a small maintenance cost and competitors lose
        # the gain captured by the active edge.
        support = [max(0.0, value - SUPPORT_DECAY) for value in support]
        support[action] = max(0.0, support[action] + max(0.0, benefit))
        support[1 - action] = max(0.0, support[1 - action] - max(0.0, benefit) * 0.35)
        energy -= ACTION_COST
        records.append((step, target, action, benefit, support[:], energy))

    helpful_before = min(range(2), key=lambda a: abs(initial_target_sign * TARGET_MAGNITUDE - effects[a]))
    helpful_after = min(range(2), key=lambda a: abs(-initial_target_sign * TARGET_MAGNITUDE - effects[a]))
    after = records[SWITCH:]
    pre = records[:SWITCH]
    post_choice = sum(r[2] == helpful_after for r in after[-40:]) / 40.0
    pre_choice = sum(r[2] == helpful_before for r in pre[-40:]) / 40.0
    final_edges = [a for a in range(2) if support[a] >= EDGE_THRESHOLD]
    recovery = next(
        (r[0] - SWITCH for r in after if r[2] == helpful_after and r[3] > 0),
        STEPS - SWITCH,
    )
    return {
        "pre_choice": pre_choice,
        "post_choice": post_choice,
        "recovery_steps": recovery,
        "final_edges": final_edges,
        "helpful_after": helpful_after,
        "final_support": support,
        "energy_remaining": energy,
    }


def summarize(mode):
    rows = [run(seed, mode) for seed in range(WORLDS)]
    return {
        "worlds": WORLDS,
        "pre_switch_helpful_choice": sum(r["pre_choice"] for r in rows) / WORLDS,
        "post_switch_helpful_choice": sum(r["post_choice"] for r in rows) / WORLDS,
        "mean_recovery_steps": sum(r["recovery_steps"] for r in rows) / WORLDS,
        "single_edge_rate": sum(len(r["final_edges"]) == 1 for r in rows) / WORLDS,
        "correct_single_edge_rate": sum(
            r["final_edges"] == [r["helpful_after"]] for r in rows
        ) / WORLDS,
        "mean_energy_remaining": sum(r["energy_remaining"] for r in rows) / WORLDS,
    }


def main():
    result = {
        "experiment": "endogenous action variability under a drifting viability target",
        "steps": STEPS,
        "switch_step": SWITCH,
        "observation_sd": OBS_SD,
        "edge_threshold": EDGE_THRESHOLD,
        "modes": {mode: summarize(mode) for mode in (
            "endogenous_uncertainty", "greedy_predictive", "passive_fixed")},
        "limitation": (
            "The viability variable, action set, and initial candidate edges are supplied; "
            "this is an identifiability/boundary toy, not evidence for biological autopoiesis."
        ),
    }
    path = Path(__file__).with_name("endogenous_wanting_probe_result.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
