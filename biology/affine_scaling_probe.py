"""Test local multiplicative versus affine homeostatic synaptic scaling.

The perturbation depresses a random subset of units.  Every condition gets
the same pre-perturbation activity target; only the homeostatic transform is
ablated.  We score restoration of activity separately from preservation of
the input code, because an affine offset can restore the mean while changing
weak/strong synapse ratios.
"""
import numpy as np


SEEDS = 100
UNITS = 64
SYNAPSES = 32
SAMPLES = 800


def make_inputs(rng, n):
    labels = rng.integers(0, 2, n)
    x = rng.uniform(0.0, 0.25, (n, SYNAPSES))
    x[labels == 0, : SYNAPSES // 2] += rng.uniform(0.7, 1.3, (np.sum(labels == 0), SYNAPSES // 2))
    x[labels == 1, SYNAPSES // 2 :] += rng.uniform(0.7, 1.3, (np.sum(labels == 1), SYNAPSES // 2))
    return x, labels


def score(w, x, labels, preferred):
    y = x @ w.T
    # Each unit has a stable downstream sign; compare its two class means.
    # This is a readout of its code, not a reward supplied to the rule.
    class_mean = np.stack((y[labels == 0].mean(axis=0),
                           y[labels == 1].mean(axis=0)))
    margin = class_mean[preferred, np.arange(w.shape[0])] - class_mean[1 - preferred, np.arange(w.shape[0])]
    accuracy = np.mean(margin > 0.0)
    activity = np.mean(y, axis=0)
    return float(accuracy), activity, float(np.mean(np.abs(margin)))


def transform(w, depressed, target, mean_x, mode):
    out = w.copy()
    current = w @ mean_x
    if mode == "local_mult":
        factor = target[depressed] / np.maximum(current[depressed], 1e-8)
        out[depressed] *= factor[:, None]
    elif mode == "global_mult":
        factor = np.mean(target) / max(float(np.mean(current)), 1e-8)
        out *= factor
    elif mode in ("local_affine", "local_add"):
        a = 0.75 if mode == "local_affine" else 1.0
        b = (target - a * current) / max(float(np.sum(mean_x)), 1e-8)
        # Only the perturbed units receive compensation; the rest are the
        # within-life control for the same target and input distribution.
        out[depressed] = a * out[depressed] + b[depressed, None]
    else:
        raise ValueError(mode)
    return np.maximum(out, 0.0)


def run(seed, mode):
    rng = np.random.default_rng(seed)
    x, labels = make_inputs(rng, SAMPLES)
    # Heterogeneous baseline rates make a single population gain an explicit
    # ablation rather than an equivalent implementation.
    preferred = rng.integers(0, 2, UNITS)
    w0 = rng.lognormal(mean=-1.0, sigma=0.45, size=(UNITS, SYNAPSES))
    boost = np.zeros_like(w0)
    boost[preferred == 0, : SYNAPSES // 2] = 0.28
    boost[preferred == 1, SYNAPSES // 2 :] = 0.28
    w0 += boost
    mean_x = x.mean(axis=0)
    baseline_activity = w0 @ mean_x
    baseline_acc, _, baseline_margin = score(w0, x, labels, preferred)

    depressed = rng.random(UNITS) < 0.5
    w_perturbed = w0.copy()
    w_perturbed[depressed] *= 0.4
    w = transform(w_perturbed, depressed, baseline_activity, mean_x, mode)
    accuracy, activity, margin = score(w, x, labels, preferred)
    ratios0 = w0 / np.maximum(w0.mean(axis=1, keepdims=True), 1e-8)
    ratios = w / np.maximum(w.mean(axis=1, keepdims=True), 1e-8)
    ratio_rmse = float(np.sqrt(np.mean((ratios - ratios0) ** 2)))
    activity_error = float(np.mean(np.abs(activity - baseline_activity)) /
                          np.maximum(np.mean(baseline_activity), 1e-8))
    return np.array([baseline_acc, accuracy, activity_error, ratio_rmse,
                     margin / max(baseline_margin, 1e-8), float(np.mean(depressed))])


def main():
    print("mode baseline_acc post_acc activity_error ratio_rmse margin_ratio depressed; 100 seeds")
    for mode in ("local_mult", "global_mult", "local_affine", "local_add"):
        rows = np.array([run(seed, mode) for seed in range(SEEDS)])
        print("%s %.6f %.6f %.6f %.6f %.6f %.6f" %
              (mode, rows[:, 0].mean(), rows[:, 1].mean(), rows[:, 2].mean(),
               rows[:, 3].mean(), rows[:, 4].mean(), rows[:, 5].mean()))


if __name__ == "__main__":
    main()
