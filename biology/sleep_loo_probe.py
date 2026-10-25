"""Compare global and leave-one-out protection during synaptic downscaling."""
import numpy as np


N_INPUTS = 100
N_TARGET = 5
PHASE_EVENTS = 600
PRE_RATE = 0.035
LOG_DECAY = 0.003
THRESHOLD = 1.2


def simulate(seed, mode, coupling):
    rng = np.random.default_rng(seed)
    weights = np.full(N_INPUTS, 0.2)
    weights[:N_TARGET] = 0.5
    total_updates = 0

    for phase in range(2):
        targets = np.zeros(N_INPUTS, dtype=bool)
        targets[phase * N_TARGET:(phase + 1) * N_TARGET] = True
        active = rng.random((PHASE_EVENTS, N_INPUTS)) < PRE_RATE
        scores = active @ weights
        signal = rng.random(PHASE_EVENTS) < (scores >= THRESHOLD)
        random_post = rng.random(PHASE_EVENTS) < signal.mean()
        post = random_post if coupling == 0 else (
            signal if coupling == 1 else (signal & (rng.random(PHASE_EVENTS) < coupling)) |
            (random_post & (rng.random(PHASE_EVENTS) >= coupling)))

        if mode == "loo":
            causal = active & ((scores[:, None] - weights[None, :] < THRESHOLD) &
                               (scores[:, None] >= THRESHOLD))
            protected = causal & post[:, None]
        elif mode == "global":
            protected = active & post[:, None]
        else:
            protected = np.zeros_like(active)

        eligible = active & ~protected
        # Keep a common budget below the eligible count in all tested conditions.
        n_updates = int(active.sum() * 0.6)
        flat = np.flatnonzero(eligible)
        chosen = flat[rng.permutation(len(flat))[:min(n_updates, len(flat))]]
        updates = np.bincount(chosen % N_INPUTS, minlength=N_INPUTS)
        total_updates += int(updates.sum())
        weights *= np.exp(-LOG_DECAY * updates)

    new = weights[N_TARGET:2 * N_TARGET].mean()
    noise = weights[np.r_[0:N_TARGET, 2 * N_TARGET:N_INPUTS]].mean()
    return new / max(noise, 1e-12), new / 0.5, noise, total_updates


def main():
    for coupling in (1.0, 0.5, 0.0):
        for mode in ("none", "global", "loo"):
            values = np.array([simulate(seed, mode, coupling) for seed in range(100)])
            mean = values.mean(axis=0)
            print("coupling=%.1f mode=%s phase_b_snr=%.6f retention=%.6f noise=%.6f "
                  "updates=%.1f snr_sd=%.6f" % (coupling, mode, mean[0], mean[1], mean[2],
                                   mean[3],
                                   values[:, 0].std(ddof=1)))


if __name__ == "__main__":
    main()
