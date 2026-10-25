"""Probe a developmental GABA-polarity switch in a recurrent microcircuit.

The same unsupervised Hebbian circuit sees noisy A/B patterns in two phases.
GABA is initially depolarizing (high intracellular chloride) and later
hyperpolarizing (lower chloride).  The probe reports recruitment and class
separation, with fixed-sign and no-GABA ablations.
"""
import numpy as np


SEEDS = 100
UNITS = 16
DIM = 32
STEPS = 1200
SWITCH = STEPS // 2


def pattern(rng, kind):
    x = rng.normal(0.0, 0.10, DIM)
    if kind == 0:
        x[: DIM // 2] += 1.0
    else:
        x[DIM // 2 :] += 1.0
    return np.maximum(x, 0.0)


def sign_for(mode, step):
    if mode == "developmental":
        return 1.0 if step < SWITCH else -1.0
    if mode == "depolarizing":
        return 1.0
    if mode == "hyperpolarizing":
        return -1.0
    if mode == "none":
        return 0.0
    raise ValueError(mode)


def response(w, x, prev, lateral, gaba_sign):
    drive = w @ x + gaba_sign * 0.30 * (lateral @ prev)
    y = np.maximum(drive, 0.0)
    scale = np.sqrt(np.mean(y * y)) + 1e-6
    return y / scale


def score(seed, mode, eta=0.002, decay=0.001):
    rng = np.random.default_rng(seed)
    w = np.maximum(rng.normal(0.15, 0.03, (UNITS, DIM)), 0.0)
    lateral = rng.normal(0.0, 0.06, (UNITS, UNITS))
    np.fill_diagonal(lateral, 0.0)
    prev = np.zeros(UNITS)
    phase_activity = [[], []]
    for step in range(STEPS):
        phase = 0 if step < SWITCH else 1
        dominant = phase
        kind = dominant if rng.random() < 0.8 else 1 - dominant
        x = pattern(rng, kind)
        y = response(w, x, prev, lateral, sign_for(mode, step))
        # Local Hebbian growth with row normalization keeps the update budget equal.
        w += eta * (y[:, None] * x[None, :] - decay * w)
        w = np.maximum(w, 0.0)
        w /= np.linalg.norm(w, axis=1, keepdims=True) + 1e-6
        lateral += 0.0005 * (np.outer(y, y) - lateral)
        np.fill_diagonal(lateral, 0.0)
        prev = y
        if step >= SWITCH - 200:
            phase_activity[0].append(y)
        if step >= STEPS - 200:
            phase_activity[1].append(y)

    def eval_class(kind):
        vals = []
        for _ in range(20):
            x = pattern(rng, kind)
            vals.append(response(w, x, np.zeros(UNITS), lateral, -1.0))
        return np.mean(vals, axis=0)

    a = eval_class(0)
    b = eval_class(1)
    separation = float(np.mean(np.abs(a - b)))
    coverage_early = float(np.mean(np.mean(np.asarray(phase_activity[0]) > 0.2, axis=0)))
    coverage_late = float(np.mean(np.mean(np.asarray(phase_activity[1]) > 0.2, axis=0)))
    old_pref = float(np.mean(a[: UNITS // 2] > b[: UNITS // 2]))
    return separation, coverage_early, coverage_late, old_pref


def main():
    print("mode separation coverage_early coverage_late old_pref; %d seeds" % SEEDS)
    for mode in ("none", "depolarizing", "hyperpolarizing", "developmental"):
        rows = np.asarray([score(seed, mode) for seed in range(SEEDS)])
        print("%s %.6f %.6f %.6f %.6f" % (mode, *rows.mean(axis=0)))

    print("robustness developmental eta decay")
    for eta, decay in ((0.001, 0.0005), (0.002, 0.001), (0.004, 0.002)):
        rows = np.asarray([score(seed, "developmental", eta, decay) for seed in range(SEEDS)])
        print("%.4f %.4f %.6f %.6f %.6f %.6f" % (eta, decay, *rows.mean(axis=0)))


if __name__ == "__main__":
    main()
