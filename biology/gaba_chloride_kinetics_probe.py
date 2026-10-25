"""Probe whether gradual chloride maturation beats an abrupt GABA sign switch."""
import numpy as np

SEEDS = 100
UNITS = 16
DIM = 32
STEPS = 1200


def pattern(rng, kind):
    x = rng.normal(0.0, 0.10, DIM)
    x[kind * (DIM // 2):(kind + 1) * (DIM // 2)] += 1.0
    return np.maximum(x, 0.0)


def response(w, x, prev, lateral, sign):
    y = np.maximum(w @ x + sign * 0.30 * (lateral @ prev), 0.0)
    return y / (np.sqrt(np.mean(y * y)) + 1e-6)


def score(seed, mode, maturation=0.5, tau=120, load=0.0):
    rng = np.random.default_rng(seed)
    w = np.maximum(rng.normal(0.15, 0.03, (UNITS, DIM)), 0.0)
    w /= np.linalg.norm(w, axis=1, keepdims=True) + 1e-6
    lateral = rng.normal(0.0, 0.06, (UNITS, UNITS))
    np.fill_diagonal(lateral, 0.0)
    prev = np.zeros(UNITS)
    chloride = 1.0
    activities = [[], []]
    for step in range(STEPS):
        phase = int(step >= STEPS // 2)
        target = 1.0 if mode == "depolarizing" else 0.0
        if mode == "kinetic":
            target = 1.0 if step < maturation * STEPS else 0.0
        if mode in ("kinetic", "depolarizing"):
            chloride += (target - chloride) / tau + load * float(np.mean(prev))
            chloride = float(np.clip(chloride, 0.0, 1.0))
            sign = 2.0 * chloride - 1.0
        elif mode == "hyperpolarizing":
            sign = -1.0
        elif mode == "none":
            sign = 0.0
        else:
            raise ValueError(mode)
        kind = phase if rng.random() < 0.8 else 1 - phase
        x = pattern(rng, kind)
        y = response(w, x, prev, lateral, sign)
        w += 0.002 * (y[:, None] * x[None, :] - 0.001 * w)
        w = np.maximum(w, 0.0)
        w /= np.linalg.norm(w, axis=1, keepdims=True) + 1e-6
        lateral += 0.0005 * (np.outer(y, y) - lateral)
        np.fill_diagonal(lateral, 0.0)
        prev = y
        if step >= STEPS // 2 - 200:
            activities[0].append(y)
        if step >= STEPS - 200:
            activities[1].append(y)

    means = []
    for k in (0, 1):
        vals = [response(w, pattern(rng, k), np.zeros(UNITS), lateral, -1.0) for _ in range(20)]
        means.append(np.mean(vals, axis=0))
    separation = float(np.mean(np.abs(means[0] - means[1])))
    coverage = [float(np.mean(np.mean(np.asarray(rows) > 0.2, axis=0))) for rows in activities]
    return separation, *coverage


def main():
    print("mode maturation tau load separation coverage_early coverage_late; %d seeds" % SEEDS)
    conditions = [("none", 0.5, 120, 0.0), ("depolarizing", 0.5, 120, 0.0),
                  ("hyperpolarizing", 0.5, 120, 0.0)]
    conditions += [("kinetic", m, 120, 0.0) for m in (0.25, 0.5, 0.75)]
    conditions += [("kinetic", 0.5, t, 0.0) for t in (30, 480)]
    conditions += [("kinetic", 0.5, 120, q) for q in (-0.0002, 0.0002)]
    for mode, maturation, tau, load in conditions:
        rows = np.asarray([score(seed, mode, maturation, tau, load) for seed in range(SEEDS)])
        print("%s %.2f %d %.4f %.6f %.6f %.6f" % (mode, maturation, tau, load, *rows.mean(axis=0)))


if __name__ == "__main__":
    main()
