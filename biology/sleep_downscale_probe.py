"""Probe input-specific sleep downscaling with a narrow post-spike gate.

The rule is intentionally dimensionless: active synapses depress during a
sleep-like phase unless their input contributes to a postsynaptic spike.
"""
import numpy as np


def run(seed, mode, n=100, target_n=5, steps=1200):
    rng = np.random.default_rng(seed)
    target = np.zeros(n, dtype=bool)
    target[:target_n] = True
    w = np.full(n, 0.20)
    w[target] = 0.50  # representation established during wake
    before = w.copy()

    for _ in range(steps):
        pre = rng.random(n) < 0.035
        drive = float(np.dot(w, pre))
        post = drive > 0.60
        if mode == "local":
            # A causal post spike protects active inputs; otherwise Up-state
            # activity depresses them. The 10 ms timing is represented by
            # the same event, while delayed spikes are tested separately.
            w[pre & (not post)] *= 0.997
        elif mode == "global":
            w *= 0.997
        elif mode == "none":
            pass
        else:
            raise ValueError(mode)
        w = np.clip(w, 0.01, 1.0)

    signal = float(w[target].mean())
    noise = float(w[~target].mean())
    snr = signal / max(noise, 1e-9)
    retention = float(np.mean(w[target] / before[target]))
    return signal, noise, snr, retention


def main():
    for mode in ("none", "global", "local"):
        vals = np.array([run(seed, mode) for seed in range(100)])
        print(
            "%s signal=%.6f noise=%.6f snr=%.6f retention=%.6f "
            "snr_sd=%.6f"
            % (mode, *vals.mean(axis=0), vals[:, 2].std(ddof=1))
        )


if __name__ == "__main__":
    main()
