"""Test bounded structural growth by probationary local synaptic contacts.

One presynaptic unit has a local neighborhood of possible postsynaptic partners,
at most K total contacts, and one of those slots is reserved for a transient
sprout. The sprout samples one currently unconnected neighbor, estimates only
its own endpoint covariance, then either stabilizes, replaces a weaker stable
contact, or retracts. Stable contacts decay/prune locally after sustained low
covariance. There is no external target identity in any update.

The target identity is used only to score the simulated wiring. This is a toy
structural-plasticity hypothesis, not a biological model or a result about
general intelligence.
"""
from __future__ import annotations

import json
import random
import statistics
from dataclasses import dataclass
from pathlib import Path

N = 8
REGIME_LENGTH = 1500
REGIMES = 8
T = REGIME_LENGTH * REGIMES
SEEDS = tuple(range(20261022, 20261042))
ALPHA = 0.02
TOTAL_CAPACITIES = (2, 3)  # includes one probationary contact
PROBE_DURATIONS = (50, 100)
PROBE_MODES = ("uniform", "coactive")
ACCEPT_THRESHOLD = 0.08
PRUNE_THRESHOLD = 0.025
PRUNE_STEPS = 100
SUPERIORITY_MARGIN = 0.0
SUSTAINED_STEPS = 50


@dataclass
class Contact:
    target: int
    mx: float
    my: float
    mxy: float
    low_streak: int = 0

    @classmethod
    def form(cls, target: int) -> "Contact":
        # Start from a neutral Bernoulli(0.5) local-rate prior. In coactive
        # mode, the event that forms a contact is selected for x=y=1 and must
        # not be counted as unbiased learning evidence.
        return cls(target, 0.5, 0.5, 0.25)

    def update(self, x: float, y: float) -> None:
        self.mx += ALPHA * (x - self.mx)
        self.my += ALPHA * (y - self.my)
        self.mxy += ALPHA * (x * y - self.mxy)
        if self.score < PRUNE_THRESHOLD:
            self.low_streak += 1
        else:
            self.low_streak = 0

    @property
    def score(self) -> float:
        return self.mxy - self.mx * self.my


def choose_probe(
    rng: random.Random,
    stable: dict[int, Contact],
    n: int,
    mode: str,
    x: float,
    y: list[float],
) -> int | None:
    available = [i for i in range(n) if i not in stable]
    if mode == "coactive":
        if x == 0.0:
            return None
        available = [i for i in available if y[i] == 1.0]
        if not available:
            return None
    return rng.choice(available) if available else None


def run(
    seed: int,
    total_capacity: int,
    null_stream: bool = False,
    probe_mode: str = "uniform",
    probe_steps: int = 100,
) -> dict:
    event_rng = random.Random(seed)
    wiring_rng = random.Random(seed ^ 0x5A17C9E3)
    stable_capacity = total_capacity - 1
    stable: dict[int, Contact] = {}
    probe: Contact | None = None
    probe_age = 0
    total_active_sum = 0
    stable_active_sum = 0
    target_active_sum = 0
    true_contacts_sum = 0
    steps_with_stable = 0
    steps_with_target = 0
    max_total_contacts = 0
    births = prunes = accepted = rejected = 0
    regime_recovered_at: list[int | None] = [None] * REGIMES
    streak = 0
    recovery_found = False

    for t in range(T):
        regime = t // REGIME_LENGTH
        within_regime = t % REGIME_LENGTH
        if within_regime == 0:
            streak = 0
            recovery_found = False

        target = None if null_stream else regime % N
        x = float(event_rng.random() < 0.5)
        y = [
            x if (target is not None and i == target)
            else float(event_rng.random() < 0.5)
            for i in range(N)
        ]

        for contact in stable.values():
            contact.update(x, y[contact.target])
        if probe is not None:
            probe.update(x, y[probe.target])
            probe_age += 1

        # A stable edge with persistently weak local evidence is pruned.
        expired = [i for i, c in stable.items() if c.low_streak >= PRUNE_STEPS]
        for i in expired:
            del stable[i]
            prunes += 1

        # A sprout stabilizes into an empty slot or replaces the weakest
        # stable contact only when its endpoint evidence is stronger.
        if probe is not None and probe_age >= probe_steps:
            weakest = min(stable.values(), key=lambda c: c.score) if stable else None
            eligible = probe.score > ACCEPT_THRESHOLD
            wins = weakest is None or probe.score > weakest.score + SUPERIORITY_MARGIN
            if eligible and (len(stable) < stable_capacity or wins):
                if len(stable) >= stable_capacity and weakest is not None:
                    del stable[weakest.target]
                    prunes += 1
                stable[probe.target] = probe
                accepted += 1
                births += 1
            else:
                rejected += 1
                prunes += 1
            probe = None
            probe_age = 0

        # Occupy the reserved growth slot immediately after a rejection,
        # acceptance, or local pruning event. No system-wide ranking is used.
        if probe is None:
            probe_target = choose_probe(wiring_rng, stable, N, probe_mode, x, y)
            if probe_target is not None:
                probe = Contact.form(probe_target)
                probe_age = 0

        # Structural observations are made after current updates and decisions.
        stable_n = len(stable)
        total_n = stable_n + int(probe is not None)
        stable_active_sum += stable_n
        total_active_sum += total_n
        max_total_contacts = max(max_total_contacts, total_n)
        steps_with_stable += int(stable_n > 0)
        if target is not None:
            has_target = target in stable
            steps_with_target += int(has_target)
            target_active_sum += int(has_target)
            true_contacts_sum += sum(i == target for i in stable)
            if not recovery_found:
                streak = streak + 1 if has_target else 0
                if streak >= SUSTAINED_STEPS:
                    regime_recovered_at[regime] = within_regime - SUSTAINED_STEPS + 1
                    recovery_found = True

    recovery = [d for d in regime_recovered_at if d is not None]
    return {
        "stable_edges_per_step": stable_active_sum / T,
        "total_contacts_per_step": total_active_sum / T,
        "max_total_contacts": max_total_contacts,
        "fraction_steps_with_stable_edge": steps_with_stable / T,
        "target_coverage": target_active_sum / T if not null_stream else None,
        "stable_edge_precision": true_contacts_sum / stable_active_sum if stable_active_sum and not null_stream else None,
        "null_fraction_steps_with_stable_edge": steps_with_stable / T if null_stream else None,
        "null_stable_edges_per_step": stable_active_sum / T if null_stream else None,
        "recovery_mean_steps_to_50_sustained": statistics.mean(recovery) if recovery else None,
        "recovery_success_fraction": len(recovery) / REGIMES if not null_stream else None,
        "births": births,
        "prunes": prunes,
        "accepted_sprouts": accepted,
        "rejected_sprouts": rejected,
    }


def mean(values: list[float | int | None]) -> float | None:
    numeric = [float(v) for v in values if v is not None]
    return statistics.mean(numeric) if numeric else None


def sd(values: list[float | int | None]) -> float | None:
    numeric = [float(v) for v in values if v is not None]
    return statistics.pstdev(numeric) if numeric else None


def main() -> dict:
    configurations = []
    for mode in PROBE_MODES:
        for probe_steps in PROBE_DURATIONS:
            for capacity in TOTAL_CAPACITIES:
                target_runs = [run(seed, capacity, False, mode, probe_steps) for seed in SEEDS]
                null_runs = [run(seed, capacity, True, mode, probe_steps) for seed in SEEDS]
                configurations.append({
                    "probe_mode": mode,
                    "probe_steps": probe_steps,
                    "total_capacity": capacity,
                    "stable_capacity": capacity - 1,
                    "target_stream": {
                        key: mean([r[key] for r in target_runs])
                        for key in (
                            "stable_edges_per_step", "total_contacts_per_step",
                            "fraction_steps_with_stable_edge", "target_coverage",
                            "stable_edge_precision", "recovery_mean_steps_to_50_sustained",
                            "recovery_success_fraction", "births", "prunes",
                        )
                    },
                    "target_coverage_sd_across_seeds": sd([r["target_coverage"] for r in target_runs]),
                    "recovery_delay_sd_across_seeds": sd([r["recovery_mean_steps_to_50_sustained"] for r in target_runs]),
                    "null_stream": {
                        "stable_edges_per_step_mean": mean([r["null_stable_edges_per_step"] for r in null_runs]),
                        "steps_with_stable_edge_fraction_mean": mean([r["null_fraction_steps_with_stable_edge"] for r in null_runs]),
                        "births_mean": mean([r["births"] for r in null_runs]),
                    },
                    "max_total_contacts_observed": max(r["max_total_contacts"] for r in target_runs + null_runs),
                })

    return {
        "experiment": "local probationary sprouting under a hard synaptic budget",
        "parameters": {
            "N": N,
            "regimes": REGIMES,
            "steps_per_regime": REGIME_LENGTH,
            "total_steps_per_seed": T,
            "seeds": list(SEEDS),
            "alpha": ALPHA,
            "total_capacities_including_probe": list(TOTAL_CAPACITIES),
            "probe_durations": list(PROBE_DURATIONS),
            "probe_modes": list(PROBE_MODES),
            "accept_threshold": ACCEPT_THRESHOLD,
            "prune_threshold": PRUNE_THRESHOLD,
            "prune_steps": PRUNE_STEPS,
            "superiority_margin": SUPERIORITY_MARGIN,
            "sustained_recovery_steps": SUSTAINED_STEPS,
        },
        "fixed_random_edge_control_coverage": 1 / N,
        "definitions": {
            "local_score": "EMA(x*y) - EMA(x)*EMA(y), stored only on extant contacts and updated from their endpoints",
            "sprout": "uniform random unconnected neighbor, or a random currently coactive unconnected neighbor; one at a time in the reserved synaptic slot",
            "stabilize": "probe score exceeds accept_threshold and either a mature slot is vacant or probe beats the weakest mature edge",
            "prune": "mature contact removed after local score remains below prune_threshold for prune_steps, or when displaced by a stronger sprout",
            "target_stream": "one target equals source in each regime; all other targets are independent Bernoulli(0.5)",
            "null_stream": "all targets are independent Bernoulli(0.5)",
        },
        "configurations": configurations,
    }


if __name__ == "__main__":
    result = main()
    output = Path(__file__).with_name("probationary_sprouting_result.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
