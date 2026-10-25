"""Toy test of synaptic tagging-and-capture against a linear trace."""

import numpy as np


N_COLORS = 3
STEPS = 240


def simulate(delay, mode, seed):
    rng = np.random.default_rng(seed)
    tag = np.zeros(N_COLORS)
    resource = 0.0
    memory = np.zeros(N_COLORS)
    target = seed % N_COLORS
    weak_t = 40
    strong_t = weak_t + int(delay)
    for t in range(STEPS):
        tag *= np.exp(-1.0 / 18.0)
        resource *= np.exp(-1.0 / 30.0)
        tag += rng.random(N_COLORS) * 0.012
        if t == weak_t:
            tag[target] += 1.0
        if t == strong_t:
            resource += 1.0
        overlap = tag * resource
        if mode == "linear":
            memory *= 0.97
            memory += 0.07 * overlap
        elif mode == "capture":
            memory *= 0.999
            captured_overlap = np.where(overlap > 0.12, overlap, 0.0)
            memory += 0.035 * captured_overlap
            # Capture is gated by a sufficiently strong local tag; weak
            # background tags do not recruit the shared resource.
            active = (memory > 0.18) & (overlap > 0.12)
            memory += active * 0.028 * memory * (1.0 - memory)
        elif mode == "no_feedback":
            memory *= 0.97
            memory += 0.035 * np.where(overlap > 0.12, overlap, 0.0)
        else:
            raise ValueError(mode)
        memory = np.clip(memory, 0.0, 1.0)
    leakage = float(memory[np.arange(N_COLORS) != target].mean())
    return float(memory[target]), leakage


def main():
    seeds = range(100)
    rows = []
    for delay in (0, 20, 60, 180):
        for mode in ("linear", "capture", "no_feedback"):
            values = np.array([simulate(delay, mode, seed) for seed in seeds])
            rows.append((delay, mode, values[:, 0].mean(), values[:, 0].std(),
                         values[:, 1].mean()))
    print("delay mode target_mean target_sd leakage_mean")
    for row in rows:
        print("%4d %-12s %.6f %.6f %.6f" % row)


if __name__ == "__main__":
    main()
