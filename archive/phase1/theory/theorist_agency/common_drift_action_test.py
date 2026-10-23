"""Paired action worlds with a visible common-mode drift channel."""
import json
import random
from pathlib import Path


def run(seed, policy, horizon=360):
    rng = random.Random(seed)
    preferred = seed % 3
    means = [[0.0] * 8 for _ in range(3)]
    energy = [0.0] * 3
    counts = [0] * 3
    drift = 0.0
    picked = []
    raw_means = [[0.0] * 8 for _ in range(3)]
    raw_energy = [0.0] * 3
    for t in range(horizon):
        if t % 17 == 0:
            drift = rng.uniform(-7.0, 7.0)
        if t < 3:
            action = t
        else:
            if policy == "random":
                action = rng.randrange(3)
            else:
                em, ee = (means, energy) if policy == "residual" else (raw_means, raw_energy)
                score = [sum(x * x for x in em[a]) / (ee[a] + 0.05)
                         + 0.35 / (counts[a] + 1) ** 0.5 for a in range(3)]
                action = max(range(3), key=score.__getitem__)
        if action == preferred:
            effect = [1.0] * 8
        elif action == (preferred + 1) % 3:
            effect = [rng.choice((-2.0, 2.0)) for _ in range(8)]
        else:
            effect = [0.0] * 8
        observed = [drift + x + rng.gauss(0, 0.2) for x in effect]
        control = drift + rng.gauss(0, 0.2)
        residual = [x - control for x in observed]
        counts[action] += 1
        n = counts[action]
        for table, vals, var_table in ((means, residual, energy),
                                       (raw_means, observed, raw_energy)):
            old = table[action]
            d2 = sum((x - m) ** 2 for x, m in zip(vals, old)) / len(vals)
            table[action] = [m + (x - m) / n for m, x in zip(old, vals)]
            var_table[action] += (d2 - var_table[action]) / n
        picked.append(action)
    return sum(a == preferred for a in picked[-240:]) / 240


rows = {name: [run(seed, name) for seed in range(40)]
        for name in ("residual", "raw", "random")}
means = {name: sum(values) / len(values) for name, values in rows.items()}
out = {"paired_worlds": 40, "horizon": 360, "late_horizon": 240,
       "late_best_action_share": means,
       "residual_minus_raw": means["residual"] - means["raw"],
       "residual_minus_random": means["residual"] - means["random"]}
path = Path(__file__).with_name("common_drift_action_test_result.json")
path.write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, sort_keys=True))
