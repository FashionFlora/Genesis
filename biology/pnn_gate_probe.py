"""Toy probe of a sensory-gated structural brake on local plasticity.

The rule is unsupervised: a unit uses only x, its response y, and the local
reconstruction residual.  It is not an organism-world candidate.
"""
import numpy as np


def _unit(seed, mode, d=24, phase_steps=600, recall_steps=200):
    rng = np.random.default_rng(seed)
    mu_a = rng.normal(size=d)
    mu_a /= np.linalg.norm(mu_a)
    mu_b = rng.normal(size=d)
    mu_b -= mu_a * np.dot(mu_a, mu_b)
    mu_b /= np.linalg.norm(mu_b)
    w = rng.normal(size=d)
    w /= np.linalg.norm(w)
    openness = 1.0
    brake = 0.0
    x_trace = np.zeros(d)
    errors = []
    gates = []

    def sample(mu):
        x = mu + 0.15 * rng.normal(size=d)
        return x / np.linalg.norm(x)

    def step(mu, learn):
        nonlocal w, openness, brake, x_trace
        x = sample(mu)
        y = float(np.dot(w, x))
        residual = float(np.linalg.norm(x - y * w))
        novelty = 1.0 - float(np.dot(x, x_trace))
        surprise = np.clip((novelty - 0.65) / 0.30, 0.0, 1.0)
        x_trace = 0.98 * x_trace + 0.02 * x
        if mode == "always":
            gate = 1.0
        elif mode == "brake_only":
            gate = max(0.0, 1.0 - brake)
        elif mode == "input_coupled":
            openness = np.clip(openness + 0.08 * (surprise - 0.02), 0.05, 1.0)
            gate = openness * max(0.0, 1.0 - brake)
        elif mode == "input_ablated":
            openness = np.clip(openness + 0.08 * (0.0 - 0.02), 0.05, 1.0)
            gate = openness * max(0.0, 1.0 - brake)
        elif mode == "frozen":
            gate = 0.0
        else:
            raise ValueError(mode)
        if learn:
            # Local Oja update, with a slowly accumulating extracellular brake.
            w += 0.08 * gate * y * (x - y * w)
            w /= max(np.linalg.norm(w), 1e-12)
            if mode == "input_coupled":
                brake = np.clip(brake + 0.0012 - 0.012 * surprise, 0.0, 0.92)
            else:
                brake = min(0.92, brake + 0.0012)
        errors.append((1.0 - abs(float(np.dot(w, mu)))) if learn else
                      (1.0 - abs(float(np.dot(w, mu)))))
        gates.append(gate)

    for _ in range(phase_steps):
        step(mu_a, True)
    a_end = float(np.mean(errors[-80:]))
    for _ in range(phase_steps):
        step(mu_b, True)
    b_end = float(np.mean(errors[-80:]))
    for _ in range(recall_steps):
        step(mu_a, False)
    a_recall = float(np.mean(errors[-recall_steps:]))
    return a_end, b_end, a_recall, float(np.mean(gates[:phase_steps])), float(np.mean(gates[phase_steps:2 * phase_steps]))


def main():
    modes = ("frozen", "always", "brake_only", "input_ablated", "input_coupled")
    for mode in modes:
        values = np.array([_unit(seed, mode) for seed in range(120)])
        print({
            "mode": mode,
            "A_end_error": round(float(values[:, 0].mean()), 6),
            "B_end_error": round(float(values[:, 1].mean()), 6),
            "A_recall_error": round(float(values[:, 2].mean()), 6),
            "gate_A": round(float(values[:, 3].mean()), 6),
            "gate_B": round(float(values[:, 4].mean()), 6),
        })


if __name__ == "__main__":
    main()
