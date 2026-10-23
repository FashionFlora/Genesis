"""Test consequence-based choice, including an action never tried in learning."""

import json
import random
from pathlib import Path


def run(seed, policy, steps=240):
    rng = random.Random(seed)
    counts = [[0.0] * 4 for _ in range(2)]
    means = [[[0.0] * 12 for _ in range(4)] for _ in range(2)]
    energy = [[0.0] * 4 for _ in range(2)]
    stable = noisy = zero = unused = 0
    # Rotate the useful action ID so success cannot come from a fixed preference.
    stable_ids = (seed % 3, (seed + 1) % 3)
    for t in range(steps):
        context = (t // 30) % 2
        if t < 9:
            action = t % 3
        elif policy == "random":
            action = rng.randrange(4)
        else:
            scores = []
            for action in range(4):
                predictable = sum(value * value for value in means[context][action])
                score = (predictable / max(energy[context][action], 1 / 8) ** 0.5
                         + 1.0 / (1.0 + counts[context][action]))
                scores.append(score)
            action = max(range(4), key=scores.__getitem__)
        if t >= 9 and action == 3:
            unused += 1
        if action == stable_ids[context]:
            delta = [1.0] * 12
            stable += int(t >= 9)
        elif action == (stable_ids[context] + 1) % 3:
            delta = [rng.choice((-2.0, 2.0)) for _ in range(12)]
            noisy += int(t >= 9)
        else:
            delta = [0.0] * 12
            zero += int(t >= 9)
        n = counts[context][action] + 1.0
        rate = 1.0 / n
        means[context][action] = [m + rate * (d - m)
                                  for m, d in zip(means[context][action], delta)]
        energy[context][action] += rate * (sum(d * d for d in delta)
                                            - energy[context][action])
        counts[context][action] = n
    return {"stable": stable, "noisy": noisy, "zero": zero, "unused": unused}


scores = {policy: [run(seed, policy) for seed in range(100)]
          for policy in ("conditioned", "random")}
late_horizon = 240 - 9
late = {policy: {key: sum(row[key] for row in rows) / len(rows)
                 for key in ("stable", "noisy", "zero", "unused")}
        for policy, rows in scores.items()}
out = {"seeds": 100, "steps": 240, "late_action_counts": late,
       "stable_gain": late["conditioned"]["stable"] - late["random"]["stable"],
       "stable_share_gain": (late["conditioned"]["stable"]
                             - late["random"]["stable"]) / late_horizon,
       "stable_choice_share": late["conditioned"]["stable"] / late_horizon,
       "unused_choice_share": late["conditioned"]["unused"] / late_horizon}
Path(__file__).with_name("intervention_closure_test_result.json").write_text(
    json.dumps(out, indent=2) + "\n")
print(json.dumps(out, sort_keys=True))
