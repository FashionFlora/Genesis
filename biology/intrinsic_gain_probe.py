"""Test local excitability homeostasis under a sensory intensity shift."""
import numpy as np


def run(seed, mode):
    rng = np.random.default_rng(seed)
    n_units, n_features = 96, 48
    patterns = rng.random((2, n_features)) < 0.25
    weights = rng.normal(0, 1, (n_units, n_features)) / np.sqrt(n_features)
    threshold = np.zeros(n_units)
    rate = np.zeros(n_units)
    target = 0.25
    records = []
    for phase, scale in enumerate((0.45, 1.0, 0.45)):
        for tick in range(300):
            label = tick % 2
            x = patterns[label].astype(float) * scale
            x += rng.normal(0, 0.08, n_features)
            drive = x @ weights.T
            y = 1 / (1 + np.exp(-np.clip(8 * (drive - threshold), -30, 30)))
            if mode == "local":
                rate += 0.02 * (y - rate)
                threshold += 0.002 * (rate - target)
            elif mode == "global":
                rate += 0.02 * (y.mean() - rate.mean())
                threshold[:] += 0.002 * (rate.mean() - target)
            if tick >= 200:
                records.append((phase, label, y.copy()))
    output = []
    for phase in range(3):
        block = [(label, y) for p, label, y in records if p == phase]
        templates = [np.mean([y for label, y in block if label == k], axis=0) for k in (0, 1)]
        correct, active = [], []
        for label, y in block:
            correct.append(np.argmin([np.mean((y - t) ** 2) for t in templates]) == label)
            active.append(y.mean())
        output.append((float(np.mean(correct)), float(np.mean(active))))
    return output


def main():
    for mode in ("fixed", "global", "local"):
        values = np.array([run(seed, mode) for seed in range(100)])
        print(mode, "accuracy", np.round(values[:, :, 0].mean(axis=0), 6).tolist(),
              "activity", np.round(values[:, :, 1].mean(axis=0), 6).tolist())


if __name__ == "__main__":
    main()
