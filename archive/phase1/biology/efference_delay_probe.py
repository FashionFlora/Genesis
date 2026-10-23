#!/usr/bin/env python3
"""Toy test: delayed action consequences need an action-tag eligibility trace."""
import json
import random
from pathlib import Path

WORLDS = 200
STEPS = 240
SWITCH = 120
DELAY = 4
NOISE = 0.08
LR = 0.12


def run(seed, mode):
    rng = random.Random(seed)
    effects = [1.0, -1.0]
    estimates = [0.0, 0.0]
    support = [0.5, 0.5]
    pending = [None] * DELAY
    correct = 0
    kept_correct = 0
    for t in range(STEPS):
        if t == SWITCH:
            effects = [-x for x in effects]
        action = rng.randrange(2)
        pending.append((action, effects[action] + rng.gauss(0, NOISE)))
        consequence = pending.pop(0)
        if consequence is not None:
            tagged_action, observed = consequence
            if mode == "tagged":
                estimates[tagged_action] += LR * (observed - estimates[tagged_action])
                chosen = min(range(2), key=lambda a: estimates[a])
                # The edge survives only when its tagged prediction is locally useful.
                for a in range(2):
                    support[a] = max(0.0, support[a] + (0.02 if estimates[a] < 0 else -0.02))
            else:
                # The control sees the same outcomes but credits the most recent action.
                estimates[action] += LR * (observed - estimates[action])
                chosen = min(range(2), key=lambda a: estimates[a])
                support = [0.5, 0.5]
            if t >= SWITCH + DELAY:
                correct += chosen == 0
                kept_correct = support[0] > support[1]
    return correct / (STEPS - SWITCH - DELAY), float(kept_correct)


def main():
    out = {}
    for mode in ("tagged", "last_action_credit"):
        rows = [run(i, mode) for i in range(WORLDS)]
        out[mode] = {
            "post_switch_choice_accuracy": sum(x[0] for x in rows) / WORLDS,
            "final_correct_edge_retention_rate": sum(x[1] for x in rows) / WORLDS,
        }
    out.update({"worlds": WORLDS, "steps": STEPS, "switch_step": SWITCH,
                "feedback_delay": DELAY, "noise_sd": NOISE,
                "note": "toy identifiability test; actions randomized and action effects supplied"})
    path = Path(__file__).with_name("efference_delay_probe_result.json")
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
