"""Test whether a scalar postsynaptic event protects unrelated coactive inputs."""
import numpy as np


N_INPUTS = 100
N_TARGET = 5
PHASE_EVENTS = 600
PRE_RATE = 0.035
BASE_LOG_DECAY = 0.003


def run(seed, offset_ms, protect):
    rng = np.random.default_rng(seed)
    weights = np.full(N_INPUTS, 0.2)
    weights[:N_TARGET] = 0.5
    for phase in range(2):
        target = np.zeros(N_INPUTS, dtype=bool)
        target[phase * N_TARGET:(phase + 1) * N_TARGET] = True
        active = rng.random((PHASE_EVENTS, N_INPUTS)) < PRE_RATE
        # A single output event depends on whether any current target input fired.
        target_event = active[:, target].any(axis=1)
        post = rng.random(PHASE_EVENTS) < np.where(target_event, 0.8, 0.02)
        priority = rng.random((PHASE_EVENTS, N_INPUTS))
        causal = 0 < offset_ms <= 20
        preserved = active & (post[:, None] if protect and causal else False)
        eligible = active & ~preserved
        count = int((active & ~post[:, None]).sum())
        candidates = np.flatnonzero(eligible)
        chosen = candidates[np.argpartition(priority.ravel()[candidates], count - 1)[:count]]
        updates = np.bincount(chosen % N_INPUTS, minlength=N_INPUTS)
        weights *= np.exp(-BASE_LOG_DECAY * updates)
    new = weights[N_TARGET:2 * N_TARGET].mean()
    noise = weights[np.r_[0:N_TARGET, 2 * N_TARGET:N_INPUTS]].mean()
    protected_noise = float((active & (post[:, None] if protect and causal else False))[:, ~target].sum())
    return new / max(noise, 1e-12), new / 0.5, noise, protected_noise


def main():
    for name, offset, protect in (("none", 10, False), ("post_10ms", 10, True),
                                  ("post_50ms", 50, True)):
        values = np.array([run(seed, offset, protect) for seed in range(100)])
        means = values.mean(axis=0)
        print("%s phase_b_snr=%.6f new_target_retention=%.6f noise=%.6f "
              "coactive_noise_protected=%.2f snr_sd=%.6f" %
              (name, means[0], means[1], means[2], means[3], values[:, 0].std(ddof=1)))


if __name__ == "__main__":
    main()
