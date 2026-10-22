"""Resource-flow ecology where prediction is learned by population turnover.

Cells carry only a source->target edge and resource mass. There is no online
parameter estimator: a cell predicts the observed target with its source bit.
The edge's population share is the learned state. A cell's resource balance
is intake minus maintenance and its own prediction error; depleted cells die,
and doubling the cell's mass funds binary fission. At each fission, one
daughter retains the parent's edge and the other samples uniformly from the
other available sources. Thus exploration has no independent mutation-rate
clock: it occurs only as a consequence of resource-funded reproduction.

This is a falsifiable toy mechanism, not a biological claim. The neutral arm
keeps the same random daughter sampling but assigns every cell the population-
mean prediction cost, removing edge-specific resource selection while
conserving total prediction-dependent expenditure at each observation.
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
    mass: float = 1.0


def _poisson(rng: random.Random, rate: float) -> int:
    if rate <= 0.0:
        return 0
    limit = exp(-rate)
    product = 1.0
    count = 0
    while product > limit:
        count += 1
        product *= rng.random()
    return count - 1


def _observation(rng: random.Random, source_count: int, active_source: int,
                 flip_probability: float):
    x = [rng.randrange(2) for _ in range(source_count)]
    y = x[active_source] ^ int(rng.random() < flip_probability)
    return x, y


def run(seed: int, condition: str, *, steps: int = 3200,
        segment_length: int = 800, schedule=(0, 1, 2, 0), source_count: int = 3,
        initial_population: int = 45, initial_sources=(0, 1),
        initial_mass: float = 1.0, substrate_inflow: float = 7.7625,
        maintenance: float = 0.10, error_cost: float = 0.25,
        flip_probability: float = 0.08):
    """Run a paired condition: selected/neutral, with/without fission novelty."""
    if condition not in {"selected_fission_variation", "neutral_random_fission",
                         "selected_clonal_fission"}:
        raise ValueError(condition)
    env_rng = random.Random(seed ^ 0xE17A)
    eco_rng = random.Random(seed ^ 0xC011)
    resource_rng = random.Random(seed ^ 0xF10A)
    cells = [Cell(initial_sources[i % len(initial_sources)], initial_mass)
             for i in range(initial_population)]
    eco_rng.shuffle(cells)
    trace = []
    total_births = total_deaths = total_novel_daughters = 0
    extinct_at = None

    for t in range(steps):
        phase = min(t // segment_length, len(schedule) - 1)
        active_source = schedule[phase]
        x, y = _observation(env_rng, source_count, active_source,
                            flip_probability)
        errors = [float(x[cell.source] != y) for cell in cells]
        mean_error = mean(errors) if errors else 0.5

        # Finite substrate packets are apportioned without a fitness ranking.
        n = len(cells)
        packets = _poisson(resource_rng, substrate_inflow) if n else 0
        intake = [0] * n
        for _ in range(packets):
            intake[resource_rng.randrange(n)] += 1

        survivors = []
        step_births = step_deaths = step_novel = 0
        for i, parent in enumerate(cells):
            prediction_error = errors[i]
            if condition == "neutral_random_fission":
                prediction_error = mean_error
            new_mass = parent.mass + intake[i] - maintenance - error_cost * prediction_error
            if new_mass <= 0.0:
                step_deaths += 1
                continue

            # Fission conserves the parent's accumulated mass. There is no
            # age schedule, separate viability score, or population cap.
            lineage = [Cell(parent.source, new_mass)]
            j = 0
            while j < len(lineage):
                cell = lineage[j]
                if cell.mass >= 2.0:
                    daughter_mass = cell.mass / 2.0
                    cell.mass = daughter_mass
                    daughter_source = cell.source
                    if condition != "selected_clonal_fission":
                        alternatives = [s for s in range(source_count)
                                        if s != cell.source]
                        daughter_source = eco_rng.choice(alternatives)
                        step_novel += 1
                    lineage.append(Cell(daughter_source, daughter_mass))
                    step_births += 1
                j += 1
            survivors.extend(lineage)

        cells = survivors
        total_births += step_births
        total_deaths += step_deaths
        total_novel_daughters += step_novel
        if not cells and extinct_at is None:
            extinct_at = t + 1

        if t % 10 == 9 or t == steps - 1:
            counts = [sum(cell.source == s for cell in cells)
                      for s in range(source_count)]
            trace.append({
                "step": t + 1,
                "phase": phase,
                "active_source": active_source,
                "population": len(cells),
                "connection_instances": len(cells),
                "distinct_connections": sum(c > 0 for c in counts),
                "source_counts": counts,
                "mean_cell_mass": mean(c.mass for c in cells) if cells else 0.0,
                "matching_source_fraction": counts[active_source] / len(cells) if cells else 0.0,
                "population_target_mse": mean(errors) if errors else 0.5,
                "births_this_interval": step_births,
                "deaths_this_interval": step_deaths,
                "novel_daughters_this_interval": step_novel,
            })

    return {
        "seed": seed, "condition": condition, "steps": steps,
        "segment_length": segment_length, "schedule": list(schedule),
        "source_count": source_count, "initial_sources": list(initial_sources),
        "initial_population": initial_population, "initial_mass": initial_mass,
        "substrate_inflow": substrate_inflow, "maintenance": maintenance,
        "error_cost": error_cost, "flip_probability": flip_probability,
        "final_population": len(cells),
        "final_distinct_connections": len({c.source for c in cells}),
        "total_births": total_births, "total_deaths": total_deaths,
        "total_novel_daughters": total_novel_daughters,
        "novel_daughters_per_birth": (total_novel_daughters / total_births
                                      if total_births else 0.0),
        "extinct_at_step": extinct_at, "trace": trace,
    }


def _window(row, low=100, high=300):
    selected = []
    for item in row["trace"]:
        phase_start = item["phase"] * row["segment_length"]
        if item["phase"] > 0 and phase_start + low <= item["step"] <= phase_start + high:
            selected.append(item)
    return selected


def summarize(rows):
    result = {"runs_per_condition": len({r["seed"] for r in rows}), "conditions": {}}
    for condition in sorted({r["condition"] for r in rows}):
        group = [r for r in rows if r["condition"] == condition]
        observations = [item for r in group for item in _window(r)]
        phase2 = [item for r in group for item in _window(r)
                  if item["phase"] == 2]
        # Phase 2 is the first time source 2 is predictive; it is absent at birth.
        # Phase 3 returns to source 0, measuring re-expression of an old edge.
        return_windows = [item for r in group for item in r["trace"]
                          if item["phase"] == 3 and 2400 <= item["step"] <= 2600]
        result["conditions"][condition] = {
            "mutation_probability_per_birth": (0.0 if condition == "selected_clonal_fission" else 1.0),
            "mean_post_shift_matching_fraction_100_300": mean(
                x["matching_source_fraction"] for x in observations) if observations else None,
            "mean_post_shift_target_mse_100_300": mean(
                x["population_target_mse"] for x in observations) if observations else None,
            "novel_source_2_share_after_its_first_shift": mean(
                x["source_counts"][2] / x["population"] if x["population"] else 0.0
                for x in phase2) if phase2 else None,
            "source_0_share_after_return": mean(
                x["source_counts"][0] / x["population"] if x["population"] else 0.0
                for x in return_windows) if return_windows else None,
            "mean_final_population": mean(r["final_population"] for r in group),
            "mean_births": mean(r["total_births"] for r in group),
            "mean_deaths": mean(r["total_deaths"] for r in group),
            "mean_novel_daughters": mean(r["total_novel_daughters"] for r in group),
            "extinctions": sum(r["extinct_at_step"] is not None for r in group),
        }
    return result


def paired_differences(rows, a, b):
    by = {(r["seed"], r["condition"]): r for r in rows}
    seeds = sorted({r["seed"] for r in rows})
    out = {}
    for label, metric in (("matching_share", "matching_source_fraction"),
                          ("target_mse", "population_target_mse")):
        diffs = []
        for seed in seeds:
            wa, wb = _window(by[(seed, a)]), _window(by[(seed, b)])
            va = mean(x[metric] for x in wa)
            vb = mean(x[metric] for x in wb)
            diffs.append(va - vb)
        out[label] = {"mean_a_minus_b": mean(diffs), "per_seed": diffs,
                      "seeds_favor_a": sum(d > 0 if label == "matching_share" else d < 0
                                            for d in diffs)}
    return out


def main():
    seeds = list(range(30))
    params = {
        "steps": 3200, "segment_length": 800, "schedule": [0, 1, 2, 0],
        "source_count": 3, "initial_population": 45, "initial_sources": [0, 1],
        "initial_mass": 1.0, "substrate_inflow": 7.7625,
        "maintenance": 0.10, "error_cost": 0.25, "flip_probability": 0.08,
        "seeds": seeds, "measurement_window_after_shift": [100, 300],
        "conditions": ["selected_fission_variation", "neutral_random_fission",
                       "selected_clonal_fission"],
    }
    rows = []
    for seed in seeds:
        for condition in params["conditions"]:
            rows.append(run(seed, condition, **{k: v for k, v in params.items()
                                                 if k in {"steps", "segment_length", "schedule",
                                                          "source_count", "initial_population",
                                                          "initial_sources", "initial_mass",
                                                          "substrate_inflow", "maintenance",
                                                          "error_cost", "flip_probability"}}))
    summary = summarize(rows)

    # Paired resource supply perturbations test whether the effect is tied to
    # the deliberately balanced starting point; no other rates are changed.
    supply_sensitivity = {}
    for factor in (0.9, 1.1):
        perturbed = []
        for seed in range(10):
            for condition in ("selected_fission_variation", "neutral_random_fission"):
                perturbed.append(run(seed, condition, **{
                    "steps": params["steps"], "segment_length": params["segment_length"],
                    "schedule": tuple(params["schedule"]), "source_count": 3,
                    "initial_population": 45, "initial_sources": (0, 1),
                    "initial_mass": 1.0, "substrate_inflow": params["substrate_inflow"] * factor,
                    "maintenance": params["maintenance"], "error_cost": params["error_cost"],
                    "flip_probability": params["flip_probability"],
                }))
        supply_sensitivity[str(factor)] = summarize(perturbed)
        supply_sensitivity[str(factor)]["paired_selected_minus_neutral"] = paired_differences(
            perturbed, "selected_fission_variation", "neutral_random_fission")
        for row in perturbed:
            row.pop("trace")
        supply_sensitivity[str(factor)]["per_seed"] = perturbed

    result = {
        "model": "population-level learning through differential persistence; no within-cell learner",
        "parameters": params,
        "summary": summary,
        "paired_selected_minus_neutral": paired_differences(
            rows, "selected_fission_variation", "neutral_random_fission"),
        "paired_selected_minus_clonal": paired_differences(
            rows, "selected_fission_variation", "selected_clonal_fission"),
        "supply_sensitivity": supply_sensitivity,
        "runs": rows,
    }
    out = Path(__file__).with_name("resource_flux_ancestry_results.json")
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"summary": summary,
                      "paired_selected_minus_neutral": result["paired_selected_minus_neutral"],
                      "paired_selected_minus_clonal": result["paired_selected_minus_clonal"],
                      "supply_sensitivity": {k: v["conditions"] for k, v in supply_sensitivity.items()},
                      "output": str(out)}, indent=2))


if __name__ == "__main__":
    main()
