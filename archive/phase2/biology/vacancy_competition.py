"""Toy check: vacancy-driven expansion can rescue a tiny surviving input."""

import random


def simulate(
    sites, survivor_sites, hours, claim_probability, target_active, seed, gate_on_inactivity
):
    rng = random.Random(seed)
    vacant = sites - survivor_sites  # Dominant input is removed at time zero.
    occupied = survivor_sites
    for _ in range(hours):
        p = claim_probability if not (gate_on_inactivity and target_active) else 0
        claimed = sum(rng.random() < p for _ in range(vacant))
        occupied += claimed
        vacant -= claimed
    return occupied == sites, occupied, target_active


if __name__ == "__main__":
    sites, hours, trials = 100, 24, 1000
    for p in (0.10, 0.20, 0.30):
        for gate in (False, True):
            for target_active in (False, True):
                recovered = 0
                final = 0
                for seed in range(trials):
                    full, occupied, _ = simulate(
                        sites, 5, hours, p, target_active, seed, gate
                    )
                    recovered += full
                    final += occupied
                policy = "inactivity_gate" if gate else "vacancy_only"
                print(
                    f"p={p:.2f} policy={policy} target_active={target_active} "
                    f"full={recovered}/{trials} mean_occupancy={final / trials:.2f}%"
                )
