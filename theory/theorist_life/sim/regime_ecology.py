"""Regime-shift test of viability-selected predictive processes.

CPU-only deterministic simulation. Each process sees one binary Markov stream,
locally learns P(x_t=1 | x_{t-1}), and gains/loses a bounded metabolic reserve
from its own pre-update predictive skill. Division copies the predictor; a
daughter may mutate its sensory niche. Capacity pressure removes the weakest
non-juvenile process. There is no task reward or gradient.
"""
from dataclasses import dataclass
import json
from pathlib import Path
import random
from statistics import mean, stdev


@dataclass
class Process:
    niche: int
    q: list[float]
    prev: int
    energy: float = 1.0
    age: int = 0
    brier: float = 0.0
    skill: float = 0.0


def run(seed: int, *, mutation_rate: float, shift: bool = True,
        steps: int = 2400, shift_at: int = 1200, capacity: int = 192,
        initial_population: int = 48, learning_rate: float = 0.12,
        metabolic_rate: float = 0.04, maintenance: float = 0.12,
        crowd_cost: float = 0.004, division_age: int = 20,
        division_threshold: float = 0.78, juvenile_age: int = 20):
    """Run one seed and return fixed-interval records plus final population.

    The two niches exchange transition statistics at the shift: niche 0 is
    persistent (flip=.03) before the shift and noisy (flip=.5) after it;
    niche 1 does the reverse. If shift=False, niche 0 stays persistent.
    """
    env_rng = random.Random(seed ^ 0xEC0106)
    eco_rng = random.Random(seed ^ 0xA11CE)
    states = [env_rng.randrange(2), env_rng.randrange(2)]
    pop = [Process(0, [0.5, 0.5], states[0]) for _ in range(initial_population)]
    births = deaths = 0
    trace = []
    for t in range(steps):
        in_second = shift and t >= shift_at
        flip = ([0.5, 0.03] if in_second else [0.03, 0.5])
        if not shift:
            flip = [0.03, 0.5]
        for n in range(2):
            if env_rng.random() < flip[n]:
                states[n] ^= 1

        # Local sensory prediction and metabolic update.
        load = crowd_cost * len(pop) / capacity
        for p in pop:
            y = states[p.niche]
            context = p.prev
            prediction = p.q[context]
            err = (prediction - y) ** 2
            skill = 1.0 - 4.0 * err  # Brier skill against a .5 predictor.
            p.brier = err
            p.skill = skill
            p.q[context] += learning_rate * (y - prediction)
            p.prev = y
            p.energy = min(1.0, max(0.0,
                p.energy + metabolic_rate * (skill - maintenance) - load))
            p.age += 1

        # Energy exhaustion causes death. The input is local; there is no
        # externally supplied objective or shared prediction error.
        before = len(pop)
        pop = [p for p in pop if p.energy > 0.02]
        deaths += before - len(pop)

        # Division is local and heritable. Energy is split between parent and
        # daughter. The daughter starts with the current state of its chosen
        # sensory niche so its context is well-defined after niche mutation.
        born = []
        for p in pop:
            if p.age >= division_age and p.energy >= division_threshold:
                p.energy *= 0.5
                p.age = 0
                n = p.niche
                if eco_rng.random() < mutation_rate:
                    n = 1 - n
                q = [min(1.0, max(0.0, v + eco_rng.gauss(0.0, 0.015))) for v in p.q]
                born.append(Process(n, q, states[n], p.energy, 0))
                births += 1
        pop.extend(born)

        # Crowding is resolved by removing the least viable mature process;
        # a newborn gets one division interval to encounter its new stream.
        while len(pop) > capacity:
            eligible = [i for i, p in enumerate(pop) if p.age >= juvenile_age]
            if not eligible:
                eligible = list(range(len(pop)))
            weakest_energy = min(pop[i].energy for i in eligible)
            weakest = [i for i in eligible if pop[i].energy == weakest_energy]
            del pop[eco_rng.choice(weakest)]
            deaths += 1

        if t % 20 == 19 or t == steps - 1:
            n0 = sum(p.niche == 0 for p in pop)
            n1 = len(pop) - n0
            mean_error = mean(p.brier for p in pop) if pop else 1.0
            trace.append({
                "step": t + 1,
                "population": len(pop),
                "niche0": n0,
                "niche1": n1,
                "fraction_niche1": n1 / len(pop) if pop else 0.0,
                "mean_brier": mean_error,
                "mean_energy": mean(p.energy for p in pop) if pop else 0.0,
            })

    return {
        "seed": seed,
        "mutation_rate": mutation_rate,
        "shift": shift,
        "steps": steps,
        "shift_at": shift_at if shift else None,
        "capacity": capacity,
        "final_population": len(pop),
        "final_niche0": sum(p.niche == 0 for p in pop),
        "final_niche1": sum(p.niche == 1 for p in pop),
        "births": births,
        "deaths": deaths,
        "trace": trace,
    }


def summarize(rows, *, shift_at=1200):
    post = [r for r in rows if r["shift"]]
    window = [x for r in post for x in r["trace"]
              if shift_at + 400 <= x["step"] <= shift_at + 800]
    end = [x for r in post for x in r["trace"] if x["step"] > shift_at + 800]
    return {
        "n": len(rows),
        "mean_final_population": mean(r["final_population"] for r in rows),
        "mean_births": mean(r["births"] for r in rows),
        "mean_deaths": mean(r["deaths"] for r in rows),
        "mean_fraction_newly_predictable_niche_at_shift_plus_400_to_800": mean(x["fraction_niche1"] for x in window) if window else None,
        "mean_fraction_niche1_late": mean(x["fraction_niche1"] for x in end) if end else None,
        "all_runs_survive": all(r["final_population"] > 0 for r in rows),
    }


if __name__ == "__main__":
    parameters = {
        "steps": 2400,
        "shift_at": 1200,
        "capacity": 192,
        "initial_population": 48,
        "flip_probabilities": {"persistent": 0.03, "unpredictable": 0.5},
        "learning_rate": 0.12,
        "metabolic_rate": 0.04,
        "maintenance": 0.12,
        "crowd_cost": 0.004,
        "division_age": 20,
        "division_threshold": 0.78,
        "juvenile_age": 20,
        "seeds": list(range(20)),
    }
    rows = []
    for mutation_rate in (0.0, 0.05):
        for seed in parameters["seeds"]:
            rows.append(run(seed, mutation_rate=mutation_rate,
                            steps=parameters["steps"], shift_at=parameters["shift_at"],
                            capacity=parameters["capacity"],
                            initial_population=parameters["initial_population"],
                            learning_rate=parameters["learning_rate"],
                            metabolic_rate=parameters["metabolic_rate"],
                            maintenance=parameters["maintenance"],
                            crowd_cost=parameters["crowd_cost"],
                            division_age=parameters["division_age"],
                            division_threshold=parameters["division_threshold"],
                            juvenile_age=parameters["juvenile_age"]))
    summaries = []
    for rate in (0.0, 0.05):
        selected = [r for r in rows if r["mutation_rate"] == rate]
        summary = summarize(selected, shift_at=parameters["shift_at"])
        summary["mutation_rate"] = rate
        summaries.append(summary)
        print(json.dumps(summary, sort_keys=True))
    output = Path(__file__).with_name("regime_ecology_results.json")
    output.write_text(json.dumps({"model": "ecological_predictor_regime_v1",
                                  "parameters": parameters,
                                  "summaries": summaries,
                                  "runs": rows}, indent=2, sort_keys=True) + "\n")
    print(f"saved_results={output}")
