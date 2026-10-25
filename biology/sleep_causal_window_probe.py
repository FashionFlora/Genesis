"""Test whether a narrow causal post-spike window allocates downscaling."""
import numpy as np


N_INPUTS = 100
N_TARGET = 5
N_EVENTS = 1200
PRE_RATE = 0.035
POST_PROB_TARGET = 0.8
POST_PROB_NOISE = 0.02
BASE_LOG_DECAY = 0.003
WINDOW_MS = 20


def run(seed, offset_ms, protect):
    rng = np.random.default_rng(seed)
    target = np.zeros(N_INPUTS, dtype=bool)
    target[:N_TARGET] = True
    weights = np.full(N_INPUTS, 0.2)
    weights[target] = 0.5
    active = rng.random((N_EVENTS, N_INPUTS)) < PRE_RATE
    post = active & (rng.random((N_EVENTS, N_INPUTS))
                     < np.where(target, POST_PROB_TARGET, POST_PROB_NOISE))
    priority = rng.random((N_EVENTS, N_INPUTS))

    causal_window = 0 < offset_ms <= WINDOW_MS
    protected = post if protect and causal_window else np.zeros_like(post)
    eligible = active & ~protected
    update_count = int((active & ~post).sum())
    candidates = np.flatnonzero(eligible)
    candidate_priority = priority.ravel()[candidates]
    chosen = candidates[np.argpartition(candidate_priority, update_count - 1)[:update_count]]
    update_counts = np.bincount(chosen % N_INPUTS, minlength=N_INPUTS)
    weights *= np.exp(-update_counts * BASE_LOG_DECAY)

    signal = float(weights[target].mean())
    noise = float(weights[~target].mean())
    return (signal, noise, signal / max(noise, 1e-12),
            float(weights[target].mean() / 0.5),
            float(update_count), float(protected.sum()),
            float(update_count * BASE_LOG_DECAY))


def main():
    conditions = (("none", 10, False), ("post_10ms", 10, True),
                  ("post_50ms", 50, True), ("post_pre_10ms", -10, True))
    for name, offset, protect in conditions:
        vals = np.array([run(seed, offset, protect) for seed in range(100)])
        means = vals.mean(axis=0)
        print("%s signal=%.6f noise=%.6f snr=%.6f retention=%.6f "
              "updates=%.2f protected=%.2f applied_log_budget=%.6f snr_sd=%.6f"
              % (name, means[0], means[1], means[2], means[3], means[4], means[5],
                 means[6], vals[:, 2].std(ddof=1)))


if __name__ == "__main__":
    main()
