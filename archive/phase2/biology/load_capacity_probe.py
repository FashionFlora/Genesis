"""Toy probe of fast load shedding paired with slow capacity growth."""


def run(demand, capacity, throttle, growth, steps):
    cumulative_shortfall = 0.0
    accepted_total = 0.0
    for _ in range(steps):
        overload = max(0.0, demand - capacity)
        accepted = demand - throttle * overload
        capacity += growth * overload
        unserved = max(0.0, accepted - capacity)
        cumulative_shortfall += unserved
        accepted_total += accepted
    return capacity, cumulative_shortfall, accepted_total


if __name__ == "__main__":
    demand, initial_capacity, growth, steps = 2.0, 1.0, 0.05, 100
    print(
        f"demand={demand:.1f} capacity0={initial_capacity:.1f} "
        f"growth={growth:.2f} steps={steps}"
    )
    for throttle in (0.0, 0.5):
        capacity, shortfall, accepted = run(
            demand, initial_capacity, throttle, growth, steps
        )
        print(
            f"throttle={throttle:.1f} capacity={capacity:.3f} "
            f"cumulative_shortfall={shortfall:.3f} accepted={accepted:.3f}"
        )
