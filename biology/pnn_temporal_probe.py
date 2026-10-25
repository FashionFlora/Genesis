"""Toy test of PNN-like plasticity gating under matched-rate temporal patterns."""
import numpy as np


def run(seed, schedule, gate_mode, dim=24, steps=600, input_noise=0.15):
    rng = np.random.default_rng(seed)
    a = rng.normal(size=dim)
    a /= np.linalg.norm(a)
    b = rng.normal(size=dim)
    b -= a * np.dot(a, b)
    b /= np.linalg.norm(b)
    w = rng.normal(size=dim)
    w /= np.linalg.norm(w)
    trace = np.zeros(dim)
    rate_trace = 0.0
    brake = 0.0
    plasticity_cost = 0.0
    gates = []
    errors = []

    def phase(mu, phase, learn):
        nonlocal w, trace, rate_trace, brake, plasticity_cost
        event_errors = []
        for t in range(steps):
            active = (t % 100 < 10) if schedule == "burst" else (t % 10 == 0)
            x = mu + input_noise * rng.normal(size=dim) if active else np.zeros(dim)
            if active:
                x /= np.linalg.norm(x)
            if gate_mode == "sensory":
                novelty = float(np.linalg.norm(x - trace)) if active else 0.0
                surprise = np.clip((novelty - 0.65) / 0.30, 0.0, 1.0)
            elif gate_mode == "rate":
                surprise = np.clip(abs(float(active) - rate_trace) / 0.30, 0.0, 1.0)
            elif gate_mode == "ablated":
                surprise = 0.0
            else:
                surprise = 1.0
            trace = 0.98 * trace + 0.02 * x
            rate_trace = 0.98 * rate_trace + 0.02 * float(active)
            brake = np.clip(brake + 0.0012 - 0.012 * surprise, 0.0, 0.92)
            gate = 1.0 if gate_mode == "always" else max(0.0, 1.0 - brake)
            if active:
                y = float(np.dot(w, x))
                if learn:
                    delta = 0.08 * gate * y * (x - y * w)
                    w += delta
                    w /= max(np.linalg.norm(w), 1e-12)
                    plasticity_cost += float(np.linalg.norm(delta))
                event_errors.append(1.0 - abs(float(np.dot(w, mu))))
                gates.append(gate)
        errors.append((phase, float(np.mean(event_errors[-8:]))))

    phase(a, "A", True)
    phase(b, "B", True)
    phase(a, "A_recall", False)
    score = dict(errors)
    return score["B"], score["A_recall"], float(np.mean(gates[60:120])), plasticity_cost


def main():
    for gate in ("sensory", "rate", "ablated", "always"):
        by_schedule = {}
        for schedule in ("regular", "burst"):
            vals = np.array([run(seed, schedule, gate) for seed in range(100)])
            by_schedule[schedule] = vals
            print({
                "gate": gate,
                "schedule": schedule,
                "B_error": round(float(vals[:, 0].mean()), 6),
                "B_sd": round(float(vals[:, 0].std(ddof=1)), 6),
                "A_recall_error": round(float(vals[:, 1].mean()), 6),
                "A_recall_sd": round(float(vals[:, 1].std(ddof=1)), 6),
                "gate_B": round(float(vals[:, 2].mean()), 6),
                "plasticity_cost": round(float(vals[:, 3].mean()), 6),
            })
        delta = by_schedule["burst"] - by_schedule["regular"]
        ci = 1.96 * delta.std(axis=0, ddof=1) / np.sqrt(len(delta))
        print({
            "gate": gate,
            "paired_delta_burst_minus_regular": [round(float(v), 6) for v in delta.mean(axis=0)],
            "delta_95ci_half_width": [round(float(v), 6) for v in ci],
        })


if __name__ == "__main__":
    main()
