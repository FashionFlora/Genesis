"""Probe a local astrocyte-like metabolic buffer.

The only teaching signal is the organism's own energy change.  A local
reservoir low-pass filters that signal before it writes an eligibility trace.
The task reverses context--action contingencies, so memory and recovery can be
measured without an externally supplied label or reward channel.
"""
import numpy as np


def run(seed, mode, steps=4500, n_context=4, n_actions=3,
        switch=(1500, 3000), noise=0.08, alpha=0.08, coupling=0.65,
        crosstalk=0.0, transfer_cost=0.0):
    rng = np.random.default_rng(seed)
    pref = np.zeros((n_context, n_actions), dtype=float)
    trace = np.zeros_like(pref)
    energy = 0.5
    reservoir = np.zeros(n_context, dtype=float)
    previous = (0, 0)
    hits = []
    # A reversal is an environmental change, while delta_energy remains the
    # only signal available to plasticity.
    maps = (np.array([0, 1, 2, 0]), np.array([2, 0, 1, 2]),
            np.array([0, 1, 2, 0]))
    for t in range(steps):
        phase = 0 if t < switch[0] else (1 if t < switch[1] else 2)
        context = int((t // 37) % n_context)
        logits = pref[context] + 0.04 * rng.standard_normal(n_actions)
        action = int(np.argmax(logits))
        if rng.random() < 0.12:  # fixed endogenous exploration
            action = int(rng.integers(n_actions))
        target = int(maps[phase][context])
        gain = 0.12 if action == target else -0.045
        raw_delta = float(gain + noise * rng.standard_normal())
        old_energy = energy
        energy = float(np.clip(energy + raw_delta, 0.0, 1.0))
        raw_delta = float(np.clip(energy - old_energy, -0.2, 0.2))

        # Astrocyte-like signal: activity-linked local storage and delayed
        # release.  The global ablation has identical storage mass but loses
        # the context-to-reservoir assignment.
        if mode == "local_shuttle":
            reservoir[context] = (1.0 - alpha) * reservoir[context] + alpha * raw_delta
            transfer = crosstalk * (reservoir.mean() - reservoir)
            reservoir += transfer
            energy = max(0.0, energy - transfer_cost * float(np.mean(np.abs(transfer))))
            metabolic_delta = (1.0 - coupling) * raw_delta + coupling * reservoir[context]
        elif mode == "global_shuttle":
            reservoir[:] = (1.0 - alpha) * reservoir + alpha * raw_delta
            metabolic_delta = (1.0 - coupling) * raw_delta + coupling * float(reservoir.mean())
        elif mode == "direct":
            metabolic_delta = raw_delta
        else:
            raise ValueError(mode)

        trace *= 0.965
        trace[previous] += 1.0
        pref *= 0.998
        pref += 0.30 * metabolic_delta * trace
        pref -= pref.mean(axis=1, keepdims=True)
        pref = np.clip(pref, -2.0, 2.0)
        hits.append((phase, int(action == target), energy))
        previous = (context, action)

    hits = np.asarray(hits)
    windows = []
    for start in (1000, 1900, 3400, 4000):
        block = hits[start:start + 400]
        windows.append(float(block[:, 1].mean()))
    # Recovery delay: first 100-step window above 0.65 after the second switch.
    recovery = hits[3000:, 1]
    delay = 1500.0
    for offset in range(0, len(recovery) - 100, 25):
        if recovery[offset:offset + 100].mean() >= 0.65:
            delay = float(offset)
            break
    return np.asarray(windows + [delay, np.std(hits[:, 2]), np.mean(np.abs(pref))])


def main():
    modes = ("direct", "local_shuttle", "global_shuttle")
    for mode in modes:
        values = np.asarray([run(seed, mode) for seed in range(200)])
        mean = values.mean(axis=0)
        sd = values.std(axis=0)
        print(mode, "acc_early/shift/recovery/late delay energy_sd pref_abs",
              *[f"{x:.6f}" for x in mean], "sd", *[f"{x:.6f}" for x in sd])
    for alpha in (0.02, 0.08, 0.20):
        values = np.asarray([run(seed, "local_shuttle", alpha=alpha)
                             for seed in range(100)])
        print("alpha", alpha, "shift/recovery/delay",
              *[f"{x:.6f}" for x in values[:, [1, 2, 4]].mean(axis=0)])
    for crosstalk in (0.0, 0.1, 0.3, 0.6, 1.0):
        values = np.asarray([run(seed, "local_shuttle", crosstalk=crosstalk)
                             for seed in range(100)])
        print("crosstalk", crosstalk, "early/shift/recovery/late/delay",
              *[f"{x:.6f}" for x in values[:, :5].mean(axis=0)],
              "sd", *[f"{x:.6f}" for x in values[:, :5].std(axis=0)])


if __name__ == "__main__":
    main()
