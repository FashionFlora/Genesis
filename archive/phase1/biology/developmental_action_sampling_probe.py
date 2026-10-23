#!/usr/bin/env python3
"""Test whether varied self-generated interventions preserve causal edge identity."""
import json
import random
from pathlib import Path

WORLDS = 200
STEPS = 140
SWITCH = 80
DELAY = 4
NOISE = 0.08
LR = 0.2
ACTIONS = (-0.18, -0.06, 0.06, 0.18)
MODES = ("varied", "greedy")


def run(seed, mode):
    rng = random.Random(seed)
    orientation = 1 if seed % 2 == 0 else -1
    estimates = [0.0] * len(ACTIONS)
    counts = [0] * len(ACTIONS)
    support = [0.0] * len(ACTIONS)
    pending = []
    chosen = []
    for t in range(STEPS):
        effects = [orientation * x for x in ACTIONS]
        if t >= SWITCH:
            effects = [-x for x in effects]
        if mode == "varied" and (t < 24 or t % len(ACTIONS) == 0):
            action = t % len(ACTIONS)
        else:
            # Need direction is supplied by the internal state; choose the action
            # predicted to move it toward zero, with support as the local trace.
            scores = [abs(estimates[a] - 0.12) if counts[a] else float("inf")
                      for a in range(len(ACTIONS))]
            action = min(range(len(ACTIONS)), key=lambda a: scores[a])
        chosen.append(action)
        pending.append((t, action, effects[action] + rng.gauss(0.0, NOISE)))
        if len(pending) > DELAY:
            issued, tagged, observed = pending.pop(0)
            counts[tagged] += 1
            estimates[tagged] += LR * (observed - estimates[tagged])
            residual = abs(observed - estimates[tagged])
            support[tagged] = 0.9 * support[tagged] + (1.0 - residual)
    true_effects = [-orientation * x for x in ACTIONS]
    best = min(range(len(ACTIONS)), key=lambda a: abs(true_effects[a] - 0.12))
    ranked = sorted(range(len(ACTIONS)), key=lambda a: abs(estimates[a] - 0.12))
    retained = {a for a, s in enumerate(support) if s > 0.8 * max(support)}
    return {
        "best_correct": int(ranked[0] == best),
        "best_post_switch_correct": int(min(range(len(ACTIONS)), key=lambda a: abs(estimates[a] - 0.12)) == best),
        "retained_best": int(best in retained),
        "retained_edges": len(retained),
        "unique_actions_first24": len(set(chosen[:24])),
    }


def main():
    rows = []
    for mode in MODES:
        outcomes = [run(seed, mode) for seed in range(WORLDS)]
        rows.append({"mode": mode, "worlds": WORLDS, **{
            key: sum(x[key] for x in outcomes) / WORLDS
            for key in ("best_correct", "best_post_switch_correct", "retained_best",
                        "retained_edges", "unique_actions_first24")
        }})
    result = {
        "steps": STEPS, "switch_step": SWITCH, "feedback_delay": DELAY,
        "noise_sd": NOISE, "learning_rate": LR, "actions": ACTIONS, "rows": rows,
        "limitation": "Synthetic need-directed actions and supplied effect reversal; no organismal growth.",
    }
    out = Path(__file__).with_name("developmental_action_sampling_probe_result.json")
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
