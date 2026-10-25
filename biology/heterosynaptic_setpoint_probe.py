"""Probe slow, local heterosynaptic depression as an E/I set-point rule.

The rule uses only the current input, the winning unit's response, and its
local synapses. It is a mechanistic toy probe, not an organism candidate.
"""
import numpy as np


def run(seed, mode, units=12, channels=24, steps=2400, rate=0.010,
        k_fraction=0.25, input_mode="clustered"):
    rng = np.random.default_rng(seed)
    # Separate excitatory and inhibitory traces let us measure balance rather
    # than treating a single signed weight as an already-balanced circuit.
    exc = rng.uniform(0.15, 0.35, (units, channels))
    inh = rng.uniform(0.05, 0.18, (units, channels))
    usage = np.zeros(units)
    phase_rows = []
    for t in range(steps):
        phase = 0 if t < steps // 2 else 1
        # Each phase repeatedly co-activates one half of the channels, with
        # independent distractors. No target label is supplied to the rule.
        start = 0 if phase == 0 else channels // 2
        active = np.zeros(channels)
        if input_mode == "clustered":
            active[start:start + channels // 2] = (rng.random(channels // 2) < 0.72)
            active += (rng.random(channels) < 0.06).astype(float)
        elif input_mode == "sparse":
            active = (rng.random(channels) < 0.12).astype(float)
        elif input_mode == "dense":
            active = (rng.random(channels) < 0.50).astype(float)
        else:
            raise ValueError(input_mode)
        active = np.clip(active, 0.0, 1.0)
        drive = (exc - inh) @ active - 1.5 * usage
        winner = int(np.argmax(drive + 1e-6 * rng.normal(size=units)))
        y = max(0.0, float(drive[winner]))
        usage *= 0.995
        usage[winner] += 0.05
        # Fast homosynaptic potentiation at the winning unit.
        eta_h = 0.018
        delta = eta_h * y * active
        exc[winner] += delta
        inh[winner] += 0.80 * delta

        if mode != "homo_only":
            inactive = active < 0.25
            # Slow heterosynaptic depression targets the strongest unpaired
            # synapses, matching the experimentally observed selectivity.
            score = exc[winner] + inh[winner]
            candidates = np.flatnonzero(inactive)
            if candidates.size:
                k = max(1, int(candidates.size * k_fraction))
                chosen = candidates[np.argsort(score[candidates])[-k:]]
                if mode == "local_slow":
                    exc[winner, chosen] *= 1.0 - rate
                    inh[winner, chosen] *= 1.0 - rate
                elif mode == "global_slow":
                    exc[winner, candidates] *= 1.0 - rate * k / candidates.size
                    inh[winner, candidates] *= 1.0 - rate * k / candidates.size
                elif mode == "shuffled_slow":
                    shuffled = rng.choice(candidates, size=k, replace=False)
                    exc[winner, shuffled] *= 1.0 - rate
                    inh[winner, shuffled] *= 1.0 - rate
                else:
                    raise ValueError(mode)

        # A mild row-local resource constraint prevents unbounded growth and
        # is identical in every condition.
        norm = np.sqrt(np.sum(exc[winner] ** 2 + inh[winner] ** 2))
        target = np.sqrt(channels * 0.25 ** 2 * 2)
        scale = target / max(norm, 1e-9)
        exc[winner] *= scale
        inh[winner] *= scale
        if t >= steps // 2:
            phase_rows.append((active, exc[winner].copy(), inh[winner].copy()))

    # Evaluate all units on clean phase patterns, plus an unseen mixture.
    def response(x):
        return np.maximum(0.0, (exc - inh) @ x)

    a = np.r_[np.ones(channels // 2), np.zeros(channels // 2)]
    b = np.r_[np.zeros(channels // 2), np.ones(channels // 2)]
    mix = np.ones(channels) * 0.5
    ra, rb, rm = response(a), response(b), response(mix)
    selectivity = float((np.max(ra) + np.max(rb)) / (2.0 * max(np.max(rm), 1e-9)))
    e = exc.mean(axis=0)
    i = inh.mean(axis=0)
    ei_corr = float(np.corrcoef(e, i)[0, 1])
    winner_balance = float(np.mean(np.abs(exc - inh) / (exc + inh + 1e-9)))
    return selectivity, ei_corr, winner_balance, float(np.mean(exc + inh))


def main():
    print("mode selectivity unseen_mix ei_corr abs_ei_bias mean_weight; 100 paired seeds")
    for mode in ("homo_only", "local_slow", "global_slow", "shuffled_slow"):
        vals = np.array([run(seed, mode) for seed in range(100)])
        print(mode, *(f"{x:.6f}" for x in vals.mean(axis=0)),
              "selectivity_sd=%.6f" % vals[:, 0].std(ddof=1))


def robustness():
    print("robust input rate k mode selectivity ei_corr abs_ei_bias; 100 paired seeds")
    for input_mode in ("clustered", "sparse", "dense"):
        for rate, k_fraction in ((0.002, 0.25), (0.010, 0.25),
                                 (0.030, 0.25), (0.010, 0.125),
                                 (0.010, 0.50)):
            for mode in ("homo_only", "local_slow"):
                vals = np.array([run(seed, mode, rate=rate,
                                     k_fraction=k_fraction,
                                     input_mode=input_mode)
                                 for seed in range(100)])
                print(input_mode, f"{rate:.3f}", f"{k_fraction:.3f}", mode,
                      *(f"{x:.6f}" for x in vals.mean(axis=0)[:3]))


if __name__ == "__main__":
    main()
    robustness()
