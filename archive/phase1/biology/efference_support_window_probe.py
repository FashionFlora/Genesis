#!/usr/bin/env python3
"""Test whether bounded action credit supports selective edge retention."""
import json
import random
from pathlib import Path

WORLDS = 200
STEPS = 240
SWITCH = 120
TAG_WINDOW = 4
EXPLORATION = 0.15
SUPPORT_STEP = 0.04


def run(seed, mode, delay, window):
    rng = random.Random(seed)
    support = [0.5, 0.5]
    effects = [1.0, 0.0]
    pending = [None] * delay
    correct = 0
    kept = 0
    edge_count = 0

    for t in range(STEPS):
        if t == SWITCH:
            effects.reverse()
        if rng.random() < EXPLORATION:
            action = rng.randrange(2)
        else:
            action = max(range(2), key=lambda a: support[a])
        outcome = float(rng.random() < effects[action])
        pending.append((action, outcome))
        feedback = pending.pop(0)

        if feedback is not None:
            tagged_action, observed = feedback
            if mode == "tagged":
                credited = tagged_action if delay <= window else None
            else:
                credited = action
            if credited is not None:
                support[credited] += SUPPORT_STEP * (observed - 0.5)
                other = 1 - credited
                support[other] -= SUPPORT_STEP * (observed - 0.5)
                support = [max(0.0, x) for x in support]
                total = sum(support)
                if total == 0:
                    support = [0.5, 0.5]
                else:
                    support = [x / total for x in support]

        if t >= SWITCH + delay:
            correct += action == 1
            kept += support[1] > support[0]
            edge_count += sum(x >= 0.05 for x in support)

    scored = STEPS - SWITCH - delay
    return correct / scored, kept / scored, edge_count / scored


def main():
    rows = []
    for delay in (1, 4, 8):
        for mode, window in (("tagged", TAG_WINDOW), ("last_action", TAG_WINDOW)):
            results = [run(seed, mode, delay, window) for seed in range(WORLDS)]
            rows.append({
                "feedback_delay": delay,
                "assignment": mode,
                "post_switch_correct_choice": sum(r[0] for r in results) / WORLDS,
                "correct_edge_retention": sum(r[1] for r in results) / WORLDS,
                "mean_edges_above_floor": sum(r[2] for r in results) / WORLDS,
            })
    result = {
        "worlds": WORLDS, "steps": STEPS, "switch_step": SWITCH,
        "exploration_probability": EXPLORATION,
        "tag_window": TAG_WINDOW,
        "support_total": 1.0, "edge_floor": 0.05,
        "support_step": SUPPORT_STEP,
        "rows": rows,
        "limitation": "Synthetic binary consequences and a hand-specified support update; no neural growth, physiology, or self-generated viability signal.",
    }
    path = Path(__file__).with_name("efference_support_window_probe_result.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
