"""Small ablation: local synaptic scaling after a release-probability insult.

This is a measurement probe, not a candidate for the organism judge.
"""
import numpy as np


def run(seed, scaling, target=0.75, n=64, d=32, steps=600, perturb_at=200):
    rng = np.random.default_rng(seed)
    w = rng.uniform(0.25, 0.75, (n, d))
    x = rng.uniform(0.0, 1.0, (steps, d))
    p_release = np.ones(steps)
    p_release[perturb_at:] = 0.4
    rates = np.zeros((steps, n))
    # Set by the unperturbed circuit's operating point; no external reward.
    for t in range(steps):
        drive = p_release[t] * (w @ x[t]) / np.sqrt(d)
        y = 1.0 - np.exp(-drive)
        rates[t] = y
        if scaling:
            # Each unit adjusts only its own incoming gain from its recent rate.
            recent = rates[max(0, t - 19): t + 1].mean(0)
            gain = np.clip(1.0 + 0.06 * (target - recent), 0.94, 1.06)
            w *= gain[:, None]
    pre = rates[perturb_at - 20:perturb_at].mean()
    post = rates[-100:].mean()
    recovery = float(np.linalg.norm(post - pre) / np.linalg.norm(pre))
    return pre.mean(), post.mean(), recovery


def main():
    for target in (0.65, 0.75, 0.85):
        for scaling in (False, True):
            vals = np.array([run(seed, scaling, target) for seed in range(20)])
            print({
                "target": target,
                "local_scaling": scaling,
                "pre_rate_mean": round(float(vals[:, 0].mean()), 6),
                "post_rate_mean": round(float(vals[:, 1].mean()), 6),
                "relative_vector_error_mean": round(float(vals[:, 2].mean()), 6),
            })


if __name__ == "__main__":
    main()
