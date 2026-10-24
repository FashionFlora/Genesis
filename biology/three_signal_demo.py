"""Toy ablation of resource level, resource delta, and movement speed.

The model is deliberately small: it checks whether the three signals have
separable effects before putting the rule into an organism candidate.
"""


def run(energies, mode, decay=0.05, update_rate=1.0):
    trace = 1.0
    previous = energies[0]
    updates = []
    speeds = []
    for energy in energies:
        delta = energy - previous
        if mode in ("separated", "level_as_delta"):
            updates.append(update_rate * (delta if mode == "separated" else energy))
        else:
            updates.append(0.0)
        if mode in ("separated", "level_as_speed"):
            speed = 0.575 if mode == "separated" else 0.25 + 0.65 * energy
        elif mode == "delta_as_speed":
            speed = 0.575 + 0.65 * delta
        else:
            speed = 0.575
        speeds.append(speed)
        trace *= 1.0 - decay * (1.0 - energy)
        previous = energy
    return trace, sum(updates), max(speeds) - min(speeds)


if __name__ == "__main__":
    low = [0.1] * 101
    high = [0.9] * 101
    pulse = [0.5, 0.7] + [0.7] * 99
    for mode in ("separated", "level_as_delta", "level_as_speed", "delta_as_speed"):
        low_result = run(low, mode)
        high_result = run(high, mode)
        pulse_result = run(pulse, mode)
        print(
            f"{mode}: low/high_retention={low_result[0]:.3f}/{high_result[0]:.3f}, "
            f"flat_update={run([0.5] * 101, mode)[1]:.3f}, "
            f"pulse(retention={pulse_result[0]:.3f}, update={pulse_result[1]:.3f}, "
            f"speed_range={pulse_result[2]:.3f})"
        )
