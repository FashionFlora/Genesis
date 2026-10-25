"""Toy test of a local BCM-like floating plasticity threshold.

The input distribution changes halfway through a life.  All conditions see
the same patterns and update budget; only the postsynaptic plasticity
threshold differs.
"""
import numpy as np


SEEDS = 100
STEPS = 2400
SWITCH = STEPS // 2


def pattern(rng, kind, d=32):
    x = rng.normal(0.0, 0.08, d)
    if kind == 0:
        x[: d // 2] += 1.0
    else:
        x[d // 2 :] += 1.0
    return np.maximum(x, 0.0)


def response(w, x):
    # Normalizing the stimulus fixes the input budget without normalizing w.
    return float(np.dot(w, x) / np.sqrt(np.dot(x, x)))


def run(seed, mode, eta=0.004, theta_rate=0.01):
    rng = np.random.default_rng(seed)
    w = rng.normal(0.05, 0.01, 32)
    # Initial theta is local to this unit, not a population target.
    theta = 0.05
    trace = []
    for step in range(STEPS):
        dominant = 0 if step < SWITCH else 1
        # Each phase has a stable but non-deterministic input distribution.
        kind = dominant if rng.random() < 0.8 else 1 - dominant
        x = pattern(rng, kind)
        y = response(w, x)
        if mode == "bcm":
            theta += theta_rate * (y * y - theta)
            drive = y * (y - theta)
        elif mode == "fixed_hebb":
            drive = y * (y - 0.05)
        elif mode == "none":
            drive = 0.0
        else:
            raise ValueError(mode)
        w += eta * drive * x / np.sqrt(np.dot(x, x))
        w = np.clip(w, -1.5, 1.5)
        if step in (SWITCH - 1, STEPS - 1):
            a = response(w, pattern(rng, 0))
            b = response(w, pattern(rng, 1))
            trace.append((a, b, float(np.linalg.norm(w)), theta))
    a0, b0, n0, t0 = trace[0]
    a1, b1, n1, t1 = trace[1]
    return np.array([a0 - b0, b1 - a1, n0, n1, t0, t1])


def main():
    print("mode phase1_margin phase2_margin retain_old_fraction norm_end theta_end; 100 seeds")
    for mode in ("none", "fixed_hebb", "bcm"):
        rows = np.array([run(seed, mode) for seed in range(SEEDS)])
        retain_old = np.mean(rows[:, 1] < 0)
        print(
            "%s %.6f %.6f %.6f %.6f %.6f"
            % (mode, rows[:, 0].mean(), rows[:, 1].mean(), retain_old,
               rows[:, 3].mean(), rows[:, 5].mean())
        )


if __name__ == "__main__":
    main()
