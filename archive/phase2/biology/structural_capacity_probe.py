"""Check the capacity feasibility bound with a minimal scalar relaxation."""


def run(target, capacity, tau, steps):
    for step in range(steps + 1):
        activity = min(target, capacity)
        error = target - activity
        if error <= 0.01:
            return step, activity, capacity
        capacity += error / tau
    return steps, min(target, capacity), capacity


if __name__ == "__main__":
    target = 0.5
    initial_capacity = 0.1
    steps = 500_000
    print(f"target={target:.2f} initial_capacity={initial_capacity:.2f}")
    print(f"fixed_capacity activity={min(target, initial_capacity):.3f} error=0.400")
    for tau in (1_000, 10_000, 100_000):
        step, activity, capacity = run(target, initial_capacity, tau, steps)
        print(
            f"tau={tau} step_to_error<=0.01={step} "
            f"activity={activity:.3f} capacity={capacity:.3f}"
        )
