"""Parameter probe for input-specific Up-state downscaling.

The biological claim is a narrow causal protection window, not a fixed digital
number.  This sweep keeps the event stream and budget identical within each
seed while varying the window, target contribution, and downscale rate.
"""
import numpy as np


N_INPUTS = 100
N_TARGET = 5
N_EVENTS = 1200
PRE_RATE = 0.035
POST_PROB_NOISE = 0.02


def run(seed, window_ms, offset_ms, protect, target_post_prob, decay):
    rng = np.random.default_rng(seed)
    target = np.zeros(N_INPUTS, dtype=bool)
    target[:N_TARGET] = True
    weights = np.full(N_INPUTS, 0.2)
    weights[target] = 0.5
    active = rng.random((N_EVENTS, N_INPUTS)) < PRE_RATE
    post_prob = np.where(target, target_post_prob, POST_PROB_NOISE)
    post = active & (rng.random((N_EVENTS, N_INPUTS)) < post_prob)
    priority = rng.random((N_EVENTS, N_INPUTS))
    in_window = 0 < offset_ms <= window_ms
    protected = post if protect and in_window else np.zeros_like(post)
    eligible = active & ~protected
    update_count = int((active & ~post).sum())
    candidates = np.flatnonzero(eligible)
    chosen = candidates[np.argpartition(priority.ravel()[candidates], update_count - 1)[:update_count]]
    counts = np.bincount(chosen % N_INPUTS, minlength=N_INPUTS)
    weights *= np.exp(-counts * decay)
    signal = float(weights[target].mean())
    noise = float(weights[~target].mean())
    return signal / max(noise, 1e-12), float(weights[target].mean() / 0.5), float(protected.sum())


def main():
    seeds = range(100)
    print("window offset protect target_prob decay snr retention protected")
    for window in (0, 5, 10, 20, 50):
        offsets = (10,) if window == 0 else (5, 10, 20, 50)
        for offset in offsets:
            for target_prob in (0.8, 0.4, 0.1):
                for decay in (0.0015, 0.003, 0.006):
                    vals = np.array([run(seed, window, offset, window > 0,
                                         target_prob, decay) for seed in seeds])
                    mean = vals.mean(axis=0)
                    print("%5d %6d %7s %10.1f %.4f %.6f %.6f %.2f" %
                          (window, offset, str(window > 0), target_prob, decay,
                           mean[0], mean[1], mean[2]))


if __name__ == "__main__":
    main()
