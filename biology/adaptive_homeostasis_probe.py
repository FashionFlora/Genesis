"""Ablation: a cell-specific remembered baseline versus a shared set point.

The baseline is estimated from the unperturbed prefix and then frozen.  This
is a probe of local memory, not an organism candidate or a reward signal.
"""
import numpy as np


def run(seed, mode, target=0.75, n=64, d=32, steps=800, perturb_at=200):
    rng = np.random.default_rng(seed)
    w = rng.uniform(0.25, 0.75, (n, d))
    x = rng.uniform(0.0, 1.0, (steps, d))
    release = np.ones(steps)
    release[perturb_at:] = 0.4
    rates = np.zeros((steps, n))
    baseline = None
    for t in range(steps):
        drive = release[t] * (w @ x[t]) / np.sqrt(d)
        rates[t] = 1.0 - np.exp(-drive)
        if t < perturb_at:
            # Slow intrinsic memory; no target or label is supplied.
            if baseline is None:
                baseline = rates[t].copy()
            else:
                baseline = 0.98 * baseline + 0.02 * rates[t]
        elif mode != "none":
            recent = rates[max(0, t - 19):t + 1].mean(0)
            setpoint = baseline if mode == "local" else np.full(n, target)
            gain = np.clip(1.0 + 0.06 * (setpoint - recent), 0.94, 1.06)
            w *= gain[:, None]
    pre = rates[perturb_at - 20:perturb_at].mean(0)
    post = rates[-100:].mean(0)
    error = np.linalg.norm(post - pre) / np.linalg.norm(pre)
    return float(pre.mean()), float(post.mean()), float(error)


def main():
    for mode in ("none", "shared", "local"):
        vals = np.array([run(seed, mode) for seed in range(20)])
        print({
            "mode": mode,
            "pre_rate_mean": round(float(vals[:, 0].mean()), 6),
            "post_rate_mean": round(float(vals[:, 1].mean()), 6),
            "relative_vector_error_mean": round(float(vals[:, 2].mean()), 6),
            "relative_vector_error_sd": round(float(vals[:, 2].std(ddof=1)), 6),
        })


if __name__ == "__main__":
    main()
