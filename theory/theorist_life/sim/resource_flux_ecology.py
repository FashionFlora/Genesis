"""Selection and structural turnover from one local resource-flow law.

The only organism-level demographic law is net substrate flux
J_i = I_i - m - lambda * prediction_error_i. Each cell's mass integrates J_i;
depletion to zero removes it, and accumulation to twice its normalized unit
mass causes binary fission. Division splits mass equally, so fission conserves
resource mass. Total resource arrives in a finite Poisson flow and is randomly
apportioned among cells. There are no fitted survival, age, or population-cap thresholds.
Each cell carries one source-to-target connection; a funded division copies
it, with random mutation at birth. Death removes that connection. The neutral
control keeps the same total prediction-dependent resource expenditure and
mutation process, but shuffles the expenditure uniformly across cells,
removing connection-specific selection.

This is a toy model and a test of a proposed abstract law, not a biological
claim. The fast predictor is an online local conditional-frequency estimator;
population abundance is the slower integrated result of birth/death flux.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from math import exp
from pathlib import Path
import random
from statistics import mean


@dataclass
class Cell:
    source: int
    # Beta-Bernoulli counts: a local, non-gradient conditional predictor.
    positive: list[int]
    seen: list[int]
    mass: float = 1.0

    def predict(self, x: int) -> float:
        return (self.positive[x] + 1.0) / (self.seen[x] + 2.0)

    def observe(self, x: int, y: int) -> None:
        self.seen[x] += 1
        self.positive[x] += y

    def offspring(self, rng: random.Random, mutation_rate: float,
                  source_count: int, daughter_mass: float) -> "Cell":
        source = self.source
        positive = self.positive.copy()
        seen = self.seen.copy()
        if rng.random() < mutation_rate:
            choices = [s for s in range(source_count) if s != source]
            source = rng.choice(choices)
            # A changed edge is a new predictive genotype; its state begins
            # at the symmetric prior and is then learned from local samples.
            positive = [0, 0]
            seen = [0, 0]
        return Cell(source, positive, seen, daughter_mass)


def _stream_row(rng: random.Random, source_count: int, active_source: int,
                flip_probability: float):
    x = [rng.randrange(2) for _ in range(source_count)]
    y = x[active_source] ^ int(rng.random() < flip_probability)
    return x, y


def _poisson(rng: random.Random, rate: float) -> int:
    """Small self-contained Poisson sampler for substrate packet arrivals."""
    if rate <= 0.0:
        return 0
    limit = exp(-rate)
    product = 1.0
    count = 0
    while product > limit:
        count += 1
        product *= rng.random()
    return count - 1


def run(seed: int, condition: str, *, steps: int = 2400,
        segment_length: int = 600, source_count: int = 3,
        schedule: tuple[int, ...] = (0, 1, 2, 0),
        initial_population: int = 45, initial_mass: float = 1.0,
        substrate_inflow: float = 7.3125,
        maintenance: float = 0.10, error_cost: float = 0.25,
        flip_probability: float = 0.08, mutation_rate: float = 0.05):
    """Run a paired seed in selected or neutral-random-mutation mode.

    In `selected`, each cell pays loss lambda*its own one-step Brier error.
    In `neutral`, the same total loss lambda*sum(error) is charged as its
    population mean to every cell, so average resource expenditure is matched
    while the association between edge identity and growth/death is removed.
    """
    if condition not in {"selected", "neutral_random_mutation",
                         "neutral_matched_mutation"}:
        raise ValueError(condition)
    env_rng = random.Random(seed ^ 0xE17A)
    eco_rng = random.Random(seed ^ 0xC011)
    resource_rng = random.Random(seed ^ 0xF10A)
    cells = [Cell(i % source_count, [0, 0], [0, 0], initial_mass)
             for i in range(initial_population)]
    eco_rng.shuffle(cells)
    trace = []
    total_births = total_deaths = total_mutations = 0
    extinct_at = None
    for t in range(steps):
        phase = min(t // segment_length, len(schedule) - 1)
        active_source = schedule[phase]
        x, y = _stream_row(env_rng, source_count, active_source,
                           flip_probability)

        # The fast error is measured before each cell's local update.
        errors = []
        for cell in cells:
            prediction = cell.predict(x[cell.source])
            errors.append((prediction - y) ** 2)
        mean_error = mean(errors) if errors else 0.25

        # One conservation law drives all demographic change. Finite resource
        # inflow arrives as unit packets and is allocated uniformly among
        # extant cells; mass integrates intake minus upkeep and prediction
        # dissipation. Unit mass is the normalization, so binary fission at
        # mass 2 creates two unit-mass daughters.
        n_before = len(cells)
        net_fluxes = []
        if n_before:
            packets = _poisson(resource_rng, substrate_inflow)
            intake = [0] * n_before
            for _ in range(packets):
                intake[resource_rng.randrange(n_before)] += 1
            for error in errors:
                i = len(net_fluxes)
                loss = error if condition == "selected" else mean_error
                net = intake[i] - maintenance - error_cost * loss
                net_fluxes.append(net)
        else:
            net_fluxes = []

        # Update predictors after their prediction; the target is a sensory
        # component, never a reward, task label, or regime identifier.
        for cell in cells:
            cell.observe(x[cell.source], y)

        survivors = []
        step_births = step_deaths = step_mutations = 0
        for i, parent in enumerate(cells):
            net = net_fluxes[i]
            new_mass = parent.mass + net
            if new_mass <= 0.0:
                # Death is depletion of integrated resource mass, not a
                # separate fitted hazard or a chosen viability threshold.
                step_deaths += 1
                continue
            parent.mass = new_mass
            lineage = [parent]
            index = 0
            # Binary fission is the conversion of accumulated resource mass
            # into two equal cells. No wall-clock age or viability score enters.
            while index < len(lineage):
                cell = lineage[index]
                if cell.mass >= 2.0:
                    daughter_mass = cell.mass / 2.0
                    cell.mass = daughter_mass
                    child = cell.offspring(eco_rng, mutation_rate,
                                           source_count, daughter_mass)
                    lineage.append(child)
                    step_births += 1
                    step_mutations += int(child.source != cell.source)
                index += 1
            survivors.extend(lineage)
        cells = survivors
        total_births += step_births
        total_deaths += step_deaths
        total_mutations += step_mutations
        if not cells and extinct_at is None:
            extinct_at = t + 1

        # Record structure and fast prediction by phase. Structural units are
        # cells; every cell carries exactly one active sensory connection.
        if t % 10 == 9 or t == steps - 1:
            counts = [sum(c.source == s for c in cells)
                      for s in range(source_count)]
            trace.append({
                "step": t + 1,
                "phase": phase,
                "active_source": active_source,
                "population": len(cells),
                "connection_instances": len(cells),
                "distinct_connections": sum(count > 0 for count in counts),
                "source_counts": counts,
                "mean_cell_mass": mean(c.mass for c in cells) if cells else 0.0,
                "matching_source_fraction": (counts[active_source] / len(cells)
                                             if cells else 0.0),
                "population_target_mse": mean(errors) if errors else 0.25,
                "births_this_interval": step_births,
                "deaths_this_interval": step_deaths,
                "mutations_this_interval": step_mutations,
            })

    return {
        "seed": seed,
        "condition": condition,
        "steps": steps,
        "segment_length": segment_length,
        "schedule": list(schedule),
        "substrate_inflow": substrate_inflow,
        "maintenance": maintenance,
        "error_cost": error_cost,
        "flip_probability": flip_probability,
        "mutation_rate": mutation_rate,
        "initial_population": initial_population,
        "initial_mass": initial_mass,
        "final_population": len(cells),
        "final_connection_instances": len(cells),
        "final_distinct_connections": len({c.source for c in cells}),
        "total_births": total_births,
        "total_deaths": total_deaths,
        "total_mutations": total_mutations,
        "extinct_at_step": extinct_at,
        "trace": trace,
    }


def summarize(rows, *, shift_window=(100, 300)):
    # Ignore phase 0 when measuring post-shift adaptation. Windows and metrics
    # are defined independently of the simulator's structural dynamics.
    low, high = shift_window
    result = {"runs_per_condition": len({r["seed"] for r in rows}), "conditions": {}}
    for condition in sorted({r["condition"] for r in rows}):
        group = [r for r in rows if r["condition"] == condition]
        window = []
        for row in group:
            for item in row["trace"]:
                phase_start = item["phase"] * row["segment_length"]
                if item["phase"] > 0 and phase_start + low <= item["step"] <= phase_start + high:
                    window.append(item)
        result["conditions"][condition] = {
            "mutation_rate": mean(r["mutation_rate"] for r in group),
            "mean_post_shift_matching_fraction_100_300": mean(
                x["matching_source_fraction"] for x in window) if window else None,
            "mean_post_shift_target_mse_100_300": mean(
                x["population_target_mse"] for x in window) if window else None,
            "mean_final_population": mean(r["final_population"] for r in group),
            "extinctions": sum(r["extinct_at_step"] is not None for r in group),
            "mean_births": mean(r["total_births"] for r in group),
            "mean_deaths": mean(r["total_deaths"] for r in group),
            "mean_mutations": mean(r["total_mutations"] for r in group),
        }
    return result


if __name__ == "__main__":
    seeds = list(range(20))
    parameters = {
        "steps": 2400,
        "segment_length": 600,
        "schedule": [0, 1, 2, 0],
        "source_count": 3,
        "initial_population": 45,
        "initial_mass": 1.0,
        "substrate_inflow": 7.3125,
        "maintenance": 0.10,
        "error_cost": 0.25,
        "flip_probability": 0.08,
        "mutation_rates": {"selected": 0.05, "neutral_random_mutation": 0.05,
                            "neutral_matched_mutation": 0.15},
        "seeds": seeds,
        "post_shift_measurement_window": [100, 300],
    }
    rows = []
    for seed in seeds:
        for condition in ("selected", "neutral_random_mutation",
                          "neutral_matched_mutation"):
            mutation_rate = parameters["mutation_rates"][condition]
            rows.append(run(seed, condition, steps=parameters["steps"],
                            segment_length=parameters["segment_length"],
                            source_count=parameters["source_count"],
                            schedule=tuple(parameters["schedule"]),
                            initial_population=parameters["initial_population"],
                            initial_mass=parameters["initial_mass"],
                            substrate_inflow=parameters["substrate_inflow"],
                            maintenance=parameters["maintenance"],
                            error_cost=parameters["error_cost"],
                            flip_probability=parameters["flip_probability"],
                            mutation_rate=mutation_rate))
    summary = summarize(rows)
    # Robustness check: alter only the total substrate supply. This tests
    # whether tracking depends on exact balance at the initial population.
    sensitivity_rows = []
    for factor in (0.9, 1.1):
        for seed in range(10):
            for condition in ("selected", "neutral_matched_mutation"):
                row = run(seed, condition, steps=parameters["steps"],
                          segment_length=parameters["segment_length"],
                          source_count=parameters["source_count"],
                          schedule=tuple(parameters["schedule"]),
                          initial_population=parameters["initial_population"],
                          initial_mass=parameters["initial_mass"],
                          substrate_inflow=parameters["substrate_inflow"] * factor,
                          maintenance=parameters["maintenance"],
                          error_cost=parameters["error_cost"],
                          flip_probability=parameters["flip_probability"],
                          mutation_rate=parameters["mutation_rates"][condition])
                row["supply_factor"] = factor
                sensitivity_rows.append(row)
    sensitivity = {}
    for factor in (0.9, 1.1):
        grouped = [r for r in sensitivity_rows if r["supply_factor"] == factor]
        sensitivity[str(factor)] = summarize(grouped)
        # Retain per-seed outcomes without duplicating time-series traces.
        for row in grouped:
            del row["trace"]
    # Canalization-style perturbations: same stream seeds and resource law,
    # but alter one kinetic coefficient or one initial condition at a time.
    perturbations = [
        ("initial_population_36", {"initial_population": 36}),
        ("initial_population_54", {"initial_population": 54}),
        ("initial_mass_0.9", {"initial_mass": 0.9}),
        ("initial_mass_1.1", {"initial_mass": 1.1}),
        ("maintenance_0.09", {"maintenance": 0.09}),
        ("maintenance_0.11", {"maintenance": 0.11}),
        ("error_cost_0.225", {"error_cost": 0.225}),
        ("error_cost_0.275", {"error_cost": 0.275}),
    ]
    reference = {r["seed"]: r for r in rows
                 if r["condition"] == "selected" and r["seed"] < 10}
    canalization = {}
    for label, override in perturbations:
        paired = []
        for seed in range(10):
            kwargs = {
                "steps": parameters["steps"],
                "segment_length": parameters["segment_length"],
                "source_count": parameters["source_count"],
                "schedule": tuple(parameters["schedule"]),
                "initial_population": parameters["initial_population"],
                "initial_mass": parameters["initial_mass"],
                "substrate_inflow": parameters["substrate_inflow"],
                "maintenance": parameters["maintenance"],
                "error_cost": parameters["error_cost"],
                "flip_probability": parameters["flip_probability"],
                "mutation_rate": parameters["mutation_rates"]["selected"],
            }
            kwargs.update(override)
            row = run(seed, "selected", **kwargs)
            window = [x for x in row["trace"] if x["phase"] > 0 and
                      x["phase"] * row["segment_length"] + 100 <= x["step"] <=
                      x["phase"] * row["segment_length"] + 300]
            reference_window = [x for x in reference[seed]["trace"]
                                if x["phase"] > 0 and
                                x["phase"] * reference[seed]["segment_length"] + 100 <= x["step"] <=
                                x["phase"] * reference[seed]["segment_length"] + 300]
            m = mean(x["matching_source_fraction"] for x in window)
            mse = mean(x["population_target_mse"] for x in window)
            base_m = mean(x["matching_source_fraction"] for x in reference_window)
            base_mse = mean(x["population_target_mse"] for x in reference_window)
            paired.append({
                "seed": seed,
                "mean_matching_fraction": m,
                "mean_target_mse": mse,
                "delta_matching_vs_reference": m - base_m,
                "delta_mse_vs_reference": mse - base_mse,
                "final_population": row["final_population"],
                "births": row["total_births"],
                "deaths": row["total_deaths"],
                "mutations": row["total_mutations"],
                "extinct_at_step": row["extinct_at_step"],
            })
        canalization[label] = {
            "parameter_change": override,
            "runs": len(paired),
            "mean_matching_fraction": mean(r["mean_matching_fraction"] for r in paired),
            "mean_target_mse": mean(r["mean_target_mse"] for r in paired),
            "paired_delta_matching_vs_reference": mean(r["delta_matching_vs_reference"] for r in paired),
            "paired_delta_mse_vs_reference": mean(r["delta_mse_vs_reference"] for r in paired),
            "mean_final_population": mean(r["final_population"] for r in paired),
            "extinctions": sum(r["extinct_at_step"] is not None for r in paired),
            "per_seed": paired,
        }
    output = Path(__file__).with_name("resource_flux_ecology_results.json")
    output.write_text(json.dumps({"model": "resource_flow_ecology_v2",
                                  "parameters": parameters,
                                  "summary": summary,
                                  "runs": rows,
                                  "supply_sensitivity": {
                                      "replicates_per_condition": 10,
                                      "factors_relative_to_primary_supply": [0.9, 1.1],
                                      "summary": sensitivity,
                                      "runs": sensitivity_rows,
                                  },
                                  "canalization_sweep": {
                                      "replicates_per_perturbation": 10,
                                      "reference": "selected condition, same seed, unperturbed parameters",
                                      "perturbations": canalization,
                                  }}, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))
    print(json.dumps({"supply_sensitivity": sensitivity}, sort_keys=True))
    print(json.dumps({"canalization_sweep": {
        label: {key: value for key, value in result.items() if key not in {"per_seed", "parameter_change"}}
        for label, result in canalization.items()}}, sort_keys=True))
    print(f"saved_results={output}")
