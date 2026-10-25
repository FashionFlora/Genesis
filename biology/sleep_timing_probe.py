"""Compare delayed post-spike protection against global/no sleep controls."""
from collections import deque

import numpy as np


def run(seed, mode, lag=1, n=100, target_n=5, steps=1200):
    rng = np.random.default_rng(seed)
    target = np.zeros(n, dtype=bool)
    target[:target_n] = True
    w = np.full(n, 0.20)
    w[target] = 0.50
    before = w.copy()
    pending = deque()

    for _ in range(steps):
        pre = rng.random(n) < 0.035
        drive = float(np.dot(w, pre))
        post = drive > 0.60
        pending.append((pre, post))
        if len(pending) > lag:
            tagged_pre, tagged_post = pending.popleft()
            if mode == "local":
                tagged_pre = tagged_pre & (not tagged_post)
                w[tagged_pre] *= 0.997
            elif mode == "global":
                w *= 0.997
            elif mode != "none":
                raise ValueError(mode)
        w = np.clip(w, 0.01, 1.0)

    signal = float(w[target].mean())
    noise = float(w[~target].mean())
    return signal, noise, signal / max(noise, 1e-9), float(np.mean(w[target] / before[target]))


def main():
    for mode, lag in (("none", 1), ("global", 1), ("local", 1), ("local", 5)):
        vals = np.array([run(seed, mode, lag) for seed in range(100)])
        print("%s lag=%d signal=%.6f noise=%.6f snr=%.6f retention=%.6f snr_sd=%.6f"
              % (mode, lag, *vals.mean(axis=0), vals[:, 2].std(ddof=1)))


if __name__ == "__main__":
    main()
