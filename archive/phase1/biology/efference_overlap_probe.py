#!/usr/bin/env python3
"""Compare delayed action attribution when sensory consequences overlap."""
import json
import random
from pathlib import Path

WORLDS = 300
STEPS = 300
SWITCH = 150
DELAY = 4
EXPLORATION = 0.2
RATE = 0.025


def run(seed, assignment):
    rng = random.Random(seed)
    estimate = [0.0, 0.0]
    support = [0.5, 0.5]
    history = [0] * DELAY
    accuracy = retained = 0
    scored = 0
    for t in range(STEPS):
        if rng.random() < EXPLORATION:
            action = rng.randrange(2)
        else:
            action = max(range(2), key=lambda a: estimate[a])
        # Each issued command leaves a delayed sensory component; recent commands overlap.
        history.append(action)
        effects = (0.8, 0.0) if t < SWITCH else (0.0, 0.8)
        feedback = sum(effects[a] for a in history[-DELAY:]) / DELAY
        feedback += rng.gauss(0, 0.15)
        if assignment == "tagged":
            credits = {history[-DELAY]: 1.0}
        elif assignment == "distributed":
            credits = {a: history[-DELAY:].count(a) / DELAY for a in set(history[-DELAY:])}
        else:
            credits = {action: 1.0}
        prediction = sum(estimate[a] * weight for a, weight in credits.items())
        error = feedback - prediction
        for credited, weight in credits.items():
            estimate[credited] += RATE * weight * error
            support[credited] = max(0.0, support[credited] + RATE * weight * error)
        total = sum(support)
        support = [x / total for x in support] if total else [0.5, 0.5]
        if t >= SWITCH + DELAY:
            accuracy += action == 1
            retained += support[1] > support[0]
            scored += 1
    return accuracy / scored, retained / scored


def main():
    rows = {}
    for mode in ("tagged", "distributed", "latest"):
        vals = [run(seed, mode) for seed in range(WORLDS)]
        rows[mode] = {
            "post_switch_action_accuracy": sum(v[0] for v in vals) / WORLDS,
            "correct_edge_retention": sum(v[1] for v in vals) / WORLDS,
        }
    result = {"worlds": WORLDS, "steps": STEPS, "switch": SWITCH,
              "delay_and_overlap_window": DELAY, "rows": rows,
              "limitation": "Synthetic linear sensory mixture; the chosen credit rule and support update are stipulated, not biological measurements."}
    path = Path(__file__).with_name("efference_overlap_probe_result.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
