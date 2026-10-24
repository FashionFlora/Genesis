"""Toy model of a decaying synaptic tag capturing a later shared resource."""

import math
import random


SEEDS = 100
TAG_TAU = 4.0
RESOURCE_TAU = 8.0
MEASURE_AT = 12.0
CAPTURE_GAIN = 1.5


def run(seed: int, condition: str) -> float:
    rng = random.Random(seed)
    resource_delay = 3.0
    if condition == "outside_window":
        resource_delay = 12.0

    tag = math.exp(-resource_delay / TAG_TAU)
    if condition == "no_tag":
        tag = 0.0

    shared_resource = 1.0 * rng.uniform(0.9, 1.1)
    if condition == "local_resource":
        shared_resource = 0.0
    resource_at_readout = shared_resource * math.exp(
        -(MEASURE_AT - resource_delay) / RESOURCE_TAU
    )

    decayed_weak_trace = math.exp(-MEASURE_AT / TAG_TAU)
    captured = CAPTURE_GAIN * tag * resource_at_readout
    return min(1.0, decayed_weak_trace + captured)


def main() -> None:
    conditions = ("tag_capture", "no_tag", "local_resource", "outside_window")
    for condition in conditions:
        values = [run(seed, condition) for seed in range(SEEDS)]
        mean = sum(values) / len(values)
        print(f"{condition}: retained_trace={mean:.3f}")


if __name__ == "__main__":
    main()
