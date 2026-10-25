"""Probe a causal post-spike window during a shift in input statistics."""
import numpy as np


N_INPUTS = 100
N_TARGET = 5
N_EVENTS = 1200
PHASE_EVENTS = N_EVENTS // 2
PRE_RATE = 0.035
POST_PROB_NOISE = 0.02
BASE_LOG_DECAY = 0.003
WINDOW_MS = 20


def _phase_targets(phase):
    target = np.zeros(N_INPUTS, dtype=bool)
    start = phase * N_TARGET
    target[start:start + N_TARGET] = True
    return target


def _apply_phase(weights, active, post, priority, target, offset_ms, protect):
    causal_window = 0 < offset_ms <= WINDOW_MS
    protected = post if protect and causal_window else np.zeros_like(post)
    eligible = active & ~protected
    update_count = int((active & ~post).sum())
    candidates = np.flatnonzero(eligible)
    chosen = candidates[np.argpartition(priority.ravel()[candidates], update_count - 1)[:update_count]]
    update_counts = np.bincount(chosen % N_INPUTS, minlength=N_INPUTS)
    weights *= np.exp(-update_counts * BASE_LOG_DECAY)
    signal = float(weights[target].mean())
    noise = float(weights[~target].mean())
    return signal / max(noise, 1e-12), float(update_count), float(protected.sum())


def run(seed, target_post_prob, offset_ms, protect):
    rng = np.random.default_rng(seed)
    weights = np.full(N_INPUTS, 0.2)
    weights[:N_TARGET] = 0.5
    phase_snr = []
    updates = []
    protected = []
    for phase in range(2):
        target = _phase_targets(phase)
        active = rng.random((PHASE_EVENTS, N_INPUTS)) < PRE_RATE
        post_prob = np.where(target, target_post_prob, POST_PROB_NOISE)
        post = active & (rng.random((PHASE_EVENTS, N_INPUTS)) < post_prob)
        priority = rng.random((PHASE_EVENTS, N_INPUTS))
        snr, n_updates, n_protected = _apply_phase(
            weights, active, post, priority, target, offset_ms, protect)
        phase_snr.append(snr)
        updates.append(n_updates)
        protected.append(n_protected)
    old_a = float(weights[:N_TARGET].mean())
    new_b = float(weights[N_TARGET:2 * N_TARGET].mean())
    return phase_snr + [old_a / 0.5, new_b / 0.5, sum(updates), sum(protected)]


def main():
    conditions = (("none", 10, False), ("post_10ms", 10, True),
                  ("post_50ms", 50, True), ("post_pre_10ms", -10, True))
    for target_prob in (0.8, 0.4, 0.1):
        print("target_post_prob=%.1f" % target_prob)
        for name, offset, protect in conditions:
            vals = np.array([run(seed, target_prob, offset, protect)
                             for seed in range(100)])
            means = vals.mean(axis=0)
            print("%s phase_a_snr=%.6f phase_b_snr=%.6f old_a_retention=%.6f "
                  "new_b_retention=%.6f updates=%.2f protected=%.2f "
                  "phase_b_snr_sd=%.6f" %
                  (name, means[0], means[1], means[2], means[3], means[4],
                   means[5], vals[:, 1].std(ddof=1)))


if __name__ == "__main__":
    main()
