#!/usr/bin/env python3
"""Sweep delayed action-effect learning over feedback noise and action persistence."""
import json
import random
from pathlib import Path

STEPS = 240
SWITCH = 120
WORLDS = 40
DELAYS = (0, 1, 4, 8)
NOISES = (0.0, 0.2, 0.5)
REPEAT_PROBS = (0.0, 0.5, 0.9)
LR = 0.12


def run(seed, delay, noise, repeat_prob, tagged):
    rng = random.Random(seed)
    effects = [1.0, -1.0]
    estimates = [0.0, 0.0]
    pending = []
    action = rng.randrange(2)
    correct = 0
    errors = []
    for t in range(STEPS):
        if t == SWITCH:
            effects = [-x for x in effects]
        if t and rng.random() >= repeat_prob:
            action = 1 - action
        pending.append((t, action, effects[action] + rng.gauss(0, noise)))
        feedback = pending.pop(0) if len(pending) > delay else None
        if feedback is not None:
            issued_at, tagged_action, observed = feedback
            credited_action = tagged_action if tagged else action
            estimates[credited_action] += LR * (observed - estimates[credited_action])
            if issued_at >= SWITCH:
                errors.append(abs(estimates[tagged_action] - effects[tagged_action]))
        if t >= SWITCH + delay:
            choice = min(range(2), key=lambda a: estimates[a])
            correct += choice == 0
    return correct / (STEPS - SWITCH - delay), sum(errors) / max(1, len(errors))


def main():
    rows = []
    for delay in DELAYS:
        for noise in NOISES:
            for repeat_prob in REPEAT_PROBS:
                for mode, tagged in (("tagged", True), ("last_action", False)):
                    runs = [run(seed, delay, noise, repeat_prob, tagged) for seed in range(WORLDS)]
                    rows.append({
                        "delay": delay, "noise_sd": noise, "repeat_probability": repeat_prob,
                        "mode": mode,
                        "post_switch_choice_accuracy": sum(x[0] for x in runs) / WORLDS,
                        "post_switch_mean_abs_effect_error": sum(x[1] for x in runs) / WORLDS,
                    })
    out = {
        "worlds_per_condition": WORLDS, "steps": STEPS, "switch_step": SWITCH,
        "learning_rate": LR, "conditions": rows,
        "note": "synthetic two-action effect reversal; action effects and reversal are supplied",
    }
    path = Path(__file__).with_name("efference_robustness_probe_result.json")
    path.write_text(json.dumps(out, indent=2) + "\n")
    for delay in DELAYS:
        subset = [r for r in rows if r["delay"] == delay]
        tagged = [r["post_switch_choice_accuracy"] for r in subset if r["mode"] == "tagged"]
        control = [r["post_switch_choice_accuracy"] for r in subset if r["mode"] == "last_action"]
        print(f"delay={delay}: tagged accuracy {sum(tagged)/len(tagged):.3f}; "
              f"last-action {sum(control)/len(control):.3f}; "
              f"conditions={len(tagged)}")
    print(f"result={path}")


if __name__ == "__main__":
    main()
