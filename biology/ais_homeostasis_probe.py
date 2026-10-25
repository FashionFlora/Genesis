"""Probe activity-dependent AIS-like intrinsic excitability.

Each unit has a fixed synaptic filter and a slow local threshold.  A gain
change in the sensory stream is the digital analogue of chronic depolarizing
or recovery conditions.  The probe compares local threshold relocation with
global threshold and synaptic scaling at equal update counts.  No labels or
external reward are used by the adaptation.
"""
import numpy as np


def run(seed, mode, n_units=48, n_in=24, n_patterns=8, steps=2400):
    rng = np.random.default_rng(seed)
    # Fixed receptive fields: the AIS rule must preserve their relative code.
    w = rng.normal(0.0, 1.0 / np.sqrt(n_in), size=(n_units, n_in))
    w_initial = w.copy()
    theta = np.zeros(n_units)
    base = rng.normal(size=(n_patterns, n_in))
    base /= np.linalg.norm(base, axis=1, keepdims=True) + 1e-8
    activity = np.zeros(n_units)
    target = 0.22
    # Three regimes, including a return to the original gain.
    regimes = ((1.0, 800), (1.8, 800), (1.0, 800))
    responses = []
    phase_theta = []
    for gain, count in regimes:
        for _ in range(count):
            p = int(rng.integers(n_patterns))
            x = gain * base[p] + rng.normal(0.0, 0.28, n_in)
            drive = (w @ x) / np.sqrt(n_in)
            # Soft spike is used only as the local calcium/activity proxy.
            y = 1.0 / (1.0 + np.exp(-4.0 * (drive - theta)))
            activity = 0.995 * activity + 0.005 * y
            if mode == "local_ais":
                theta += 0.004 * (activity - target)
            elif mode == "global_ais":
                theta += 0.004 * (float(activity.mean()) - target)
            elif mode == "synaptic_scale":
                # Equal local activity feedback, but it changes the code.
                w *= np.exp(-0.004 * (activity - target))[:, None]
            elif mode == "ais_burst":
                # Burst-sensitive calcium proxy: same mean rate can differ in
                # temporal clustering, as in the biological AIS experiment.
                burst = np.maximum(y - 0.5, 0.0) ** 2
                theta += 0.002 * (activity - target) + 0.002 * (burst - 0.08)
            if len(responses) < 400 or _ >= count - 200:
                responses.append((p, y.copy(), gain))
        phase_theta.append(float(theta.mean()))

    # Evaluate a held-out set at each gain.  Same patterns at gain 1 test
    # reversible recovery; pairwise margins test whether code collapsed.
    test = []
    for gain in (1.0, 1.8, 1.0):
        for p in range(n_patterns):
            for _ in range(20):
                x = gain * base[p] + rng.normal(0.0, 0.28, n_in)
                drive = (w @ x) / np.sqrt(n_in)
                y = 1.0 / (1.0 + np.exp(-4.0 * (drive - theta)))
                test.append((gain, p, y))
    # Fisher-style class separability and gain invariance of population code.
    by_gain = {}
    for gain, p, y in test:
        by_gain.setdefault(gain, {}).setdefault(p, []).append(y)
    cent = {g: np.array([np.mean(by_gain[g][p], axis=0) for p in range(n_patterns)])
            for g in by_gain}
    within = float(np.mean([np.mean(np.var(by_gain[g][p], axis=0))
                            for g in by_gain for p in range(n_patterns)]))
    between = float(np.mean([np.mean((cent[1.0][i] - cent[1.0][j]) ** 2)
                             for i in range(n_patterns) for j in range(i)]))
    # Gain invariance is the correlation between the same latent pattern.
    invariance = float(np.mean([
        np.corrcoef(cent[1.0][p], cent[1.8][p])[0, 1]
        for p in range(n_patterns)
    ]))
    code_change = float(np.sqrt(np.mean((w - w_initial) ** 2)))
    weight_norm_ratio = float(np.mean(np.linalg.norm(w, axis=1) /
                                      (np.linalg.norm(w_initial, axis=1) + 1e-8)))
    return {
        "invariance": invariance,
        "separability": between / (within + 1e-9),
        "within_noise": within,
        "mean_rate": float(np.mean([y.mean() for _, _, y in test])),
        "theta_sd": float(theta.std()),
        "code_change": code_change,
        "weight_norm_ratio": weight_norm_ratio,
        "theta_high_shift": phase_theta[1] - phase_theta[0],
        "theta_recovery_error": abs(phase_theta[2] - phase_theta[0]),
    }


def main():
    modes = ("none", "local_ais", "global_ais", "synaptic_scale", "ais_burst")
    for mode in modes:
        vals = [run(seed, mode) for seed in range(200)]
        print({"mode": mode, **{k: round(float(np.mean([v[k] for v in vals])), 6)
                               for k in vals[0]}})


if __name__ == "__main__":
    main()
