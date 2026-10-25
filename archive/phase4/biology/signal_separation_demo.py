"""Arithmetic check for separating a resource state from its change signal."""


def retention(level, steps=100, decay=0.05):
    trace = 1.0
    for _ in range(steps):
        trace *= 1.0 - decay * (1.0 - level)
    return trace


def delta_updates(energies, eligibility=1.0, rate=1.0):
    weight = 0.0
    previous = energies[0]
    for energy in energies[1:]:
        weight += rate * (energy - previous) * eligibility
        previous = energy
    return weight


if __name__ == "__main__":
    low, high = retention(0.1), retention(0.9)
    flat_delta = delta_updates([0.5] * 101)
    pulse_delta = delta_updates([0.5, 0.7, 0.7])
    print(f"retention after 100 steps: low_state={low:.3f} high_state={high:.3f}")
    print(f"association update: flat_energy={flat_delta:.3f} positive_pulse={pulse_delta:.3f}")
