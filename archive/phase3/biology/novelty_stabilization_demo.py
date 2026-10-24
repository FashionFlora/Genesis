"""Toy check of novelty-gated growth and local stabilization.

This is a rule demonstration, not an organism-judge result. A unit sees two
successive input ensembles. Prediction error opens a short growth window;
repeated pre/post co-activity increases a spine's stability.
"""
from __future__ import annotations

import numpy as np


def run(novelty_gate: bool, seed: int = 7) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    n_inputs, steps = 40, 120
    active = np.zeros((steps, n_inputs), dtype=bool)
    active[:60, :8] = True
    active[60:, 8:16] = True

    # Existing synapses are deliberately sparse; new ones can grow locally.
    present = np.zeros(n_inputs, dtype=bool)
    stability = np.zeros(n_inputs, dtype=float)
    prediction = np.zeros(n_inputs, dtype=float)
    formed_at_switch = 0
    retained_from_switch = 0

    for t in range(steps):
        x = active[t].astype(float)
        novelty = np.mean(np.abs(x - prediction))
        prediction = 0.9 * prediction + 0.1 * x

        # The source reports 4.7% baseline and 10.6% after novel training.
        p_form = 0.047 + (0.106 - 0.047) * min(1.0, novelty / 0.2)
        if not novelty_gate:
            p_form = 0.047
        candidates = np.flatnonzero(x > 0.0)
        for i in candidates:
            if not present[i] and rng.random() < p_form:
                present[i] = True
                stability[i] = 0.05
                if t == 60:
                    formed_at_switch += 1

        # Local use stabilizes active synapses; unused weak ones decay.
        stability[present & (x > 0)] += 0.08
        stability[present & (x == 0)] *= 0.98
        dead = present & (stability < 0.01)
        present[dead] = False
        stability[dead] = 0.0

    retained_from_switch = int(np.sum(present[8:16]))
    return {
        "formed_at_novel_switch": float(formed_at_switch),
        "retained_novel_inputs": float(retained_from_switch),
        "final_synapses": float(np.sum(present)),
    }


if __name__ == "__main__":
    for gate in (True, False):
        vals = [run(gate, seed) for seed in range(20)]
        mean = {k: np.mean([v[k] for v in vals]) for k in vals[0]}
        print(f"novelty_gate={gate} " + " ".join(f"{k}={v:.3f}" for k, v in mean.items()))
