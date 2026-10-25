"""Illustrate BCM-style sliding plasticity threshold; not a biological fit."""


def run(adaptive: bool) -> tuple[float, float, float]:
    threshold = 0.2
    frozen_threshold = threshold
    rate = 0.01
    for activity in [0.2] * 100 + [0.8] * 100:
        if adaptive:
            threshold += rate * (activity - threshold)
    test_output = 0.5
    used_threshold = threshold if adaptive else frozen_threshold
    plasticity = test_output * (test_output - used_threshold)
    return threshold, used_threshold, plasticity


for enabled in (False, True):
    final_threshold, used_threshold, plasticity = run(enabled)
    label = "sliding" if enabled else "frozen"
    print(
        f"{label}: final_threshold={final_threshold:.3f}; "
        f"test_threshold={used_threshold:.3f}; plasticity={plasticity:+.3f}"
    )
