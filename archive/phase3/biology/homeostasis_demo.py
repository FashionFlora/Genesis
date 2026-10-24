"""Toy check of multiplicative homeostatic synaptic scaling.

This is a rule check, not organism-judge evidence. The target is a local
running activity set point; common gain scaling keeps relative strengths.
"""


def run(homeostasis=True, cycles=100):
    weights = [0.8, 0.2]
    ratios = []
    for _ in range(cycles):
        weights[0] *= 1.03  # A local correlation event strengthens one input.
        activity = sum(weights)
        if homeostasis and activity > 1e-12:
            gain = 1.0 / activity
            weights = [w * gain for w in weights]
        ratios.append(weights[0] / max(weights[1], 1e-12))
    return weights, ratios


if __name__ == "__main__":
    for enabled in (True, False):
        weights, ratios = run(enabled)
        label = "scaling" if enabled else "no_scaling"
        print(
            f"{label}: w0={weights[0]:.6f} w1={weights[1]:.6f} "
            f"activity={sum(weights):.6f} ratio_start={ratios[0]:.3f} "
            f"ratio_end={ratios[-1]:.3f}"
        )
