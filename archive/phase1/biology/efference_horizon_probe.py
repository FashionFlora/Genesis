#!/usr/bin/env python3
"""Toy test of action attribution when sensory feedback latency varies."""
import json
import random
from pathlib import Path

WORLDS = 300
STEPS = 400
MAX_DELAY = 8
NOISE = 0.25
LR = 0.12


def run(seed):
    rng = random.Random(seed)
    effects = (1.0, -1.0)
    estimates = {mode: [0.0, 0.0] for mode in ("tagged_copy", "fixed_lag_4", "current_action")}
    pending = []
    action_history = []
    correct = {mode: 0 for mode in estimates}
    total = 0
    for t in range(STEPS):
        action = rng.randrange(2)
        action_history.append(action)
        delay = rng.randint(1, MAX_DELAY)
        pending.append((t + delay, action, effects[action] + rng.gauss(0, NOISE)))
        due, pending = [event for event in pending if event[0] == t], [event for event in pending if event[0] > t]
        for _, tagged_action, observed in due:
            for mode, values in estimates.items():
                if mode == "tagged_copy":
                    credited_action = tagged_action
                elif mode == "fixed_lag_4":
                    credited_action = action_history[max(0, t - 4)]
                else:
                    credited_action = action
                values[credited_action] += LR * (observed - values[credited_action])
                chosen = min(range(2), key=lambda a: values[a])
                if t >= MAX_DELAY:
                    correct[mode] += chosen == 1
            if t >= MAX_DELAY:
                total += 1
    return {mode: count / total for mode, count in correct.items()}


def main():
    rows = [run(seed) for seed in range(WORLDS)]
    result = {
        "worlds": WORLDS,
        "steps_per_world": STEPS,
        "feedback_delay_steps": [1, MAX_DELAY],
        "action_effects": [1.0, -1.0],
        "noise_sd": NOISE,
        "post_warmup_correct_action_rate": {
            mode: sum(row[mode] for row in rows) / WORLDS
            for mode in rows[0]
        },
        "note": "synthetic stationary two-action attribution test; actions are randomized and effects supplied",
    }
    path = Path(__file__).with_name("efference_horizon_probe_result.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
