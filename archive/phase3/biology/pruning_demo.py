"""Toy check: local spike-timing correlation plus competition can prune a lagged input."""

from math import exp


def run(offset, cycles=20):
    weights = [0.5, 0.5]
    # The postsynaptic event follows input A by one tick. The Gaussian trace is
    # a deliberately simple illustration, not a fit to a biological STDP curve.
    for _ in range(cycles):
        scores = [exp(-((lag - 1) / 1.0) ** 2 / 2) for lag in (1, 1 + offset)]
        weights = [w * exp(0.8 * score) for w, score in zip(weights, scores)]
        total = sum(weights)
        weights = [w / total for w in weights]
        weights = [0.0 if w < 0.05 else w for w in weights]
        total = sum(weights)
        if total:
            weights = [w / total for w in weights]
    return weights


if __name__ == "__main__":
    for label, lag in (("synchronous", 0), ("offset_by_4_ticks", 4)):
        weights = run(lag)
        print(f"{label}: A={weights[0]:.3f}, B={weights[1]:.3f}")
