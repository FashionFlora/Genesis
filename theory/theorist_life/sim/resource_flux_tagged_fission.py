"""Can typed substrate flow generate structural variation without mutation?

This follow-up treats substrate as a finite measure over candidate edge types.
Each unit packet carries a uniformly sampled source label and is delivered to
one extant process. A cell accumulates ordinary scalar mass for viability; it
also retains the label of the most recently delivered packet. When mass-funded
fission occurs, one daughter inherits the parental edge and the other receives
that packet's edge label. No per-birth mutation probability is used. A matched
control uses the same finite resource flow and the same packet labels but
draws the daughter's edge independently, testing whether packet identity adds
anything beyond random variation at fission.

The model remains an explicit hypothesis about what resource packets encode:
uniformly available source-edge material. It is not a biological fact.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from math import exp
from pathlib import Path
import random
from statistics import mean, stdev


@dataclass
class Cell:
    source: int
    mass: float = 1.0


def poisson(rng: random.Random, rate: float) -> int:
    if rate <= 0.0:
        return 0
    stop, product, count = exp(-rate), 1.0, 0
    while product > stop:
        count += 1
        product *= rng.random()
    return count - 1


def observe(rng: random.Random, source_count: int, active_source: int,
            flip_probability: float):
    x = [rng.randrange(2) for _ in range(source_count)]
    y = x[active_source] ^ int(rng.random() < flip_probability)
    return x, y


def run(seed, condition, *, steps=3200, segment_length=800,
        schedule=(0, 1, 2, 0), source_count=3, initial_population=45,
        initial_sources=(0, 1), initial_mass=1.0, substrate_inflow=7.7625,
        maintenance=0.10, error_cost=0.25, flip_probability=0.08):
    if condition not in {"selected_tagged_fission", "neutral_tagged_fission",
                         "selected_untyped_fission", "selected_clonal_fission"}:
        raise ValueError(condition)
    env_rng = random.Random(seed ^ 0xE17A)
    eco_rng = random.Random(seed ^ 0xC011)
    inflow_rng = random.Random(seed ^ 0xF10A)
    routing_rng = random.Random(seed ^ 0xA110)
    label_rng = random.Random(seed ^ 0x1ABE)
    untyped_rng = random.Random(seed ^ 0xA11CE)
    cells = [Cell(initial_sources[i % len(initial_sources)], initial_mass)
             for i in range(initial_population)]
    eco_rng.shuffle(cells)
    trace = []
    births = deaths = packet_total = variant_daughters = 0
    packet_labels_total = [0] * source_count
    extinct_at = None

    for t in range(steps):
        phase = min(t // segment_length, len(schedule) - 1)
        active_source = schedule[phase]
        x, y = observe(env_rng, source_count, active_source, flip_probability)
        errors = [float(x[cell.source] != y) for cell in cells]
        average_error = mean(errors) if errors else 0.5

        n = len(cells)
        count = poisson(inflow_rng, substrate_inflow) if n else 0
        intake = [0] * n
        last_packet_label = [None] * n
        for _ in range(count):
            # Separate substreams keep packet counts and packet labels exactly
            # paired across conditions, even when their populations diverge.
            idx = int(routing_rng.random() * n)
            label = label_rng.randrange(source_count)
            intake[idx] += 1
            last_packet_label[idx] = label
            packet_labels_total[label] += 1

        survivors = []
        step_births = step_deaths = step_variants = 0
        for i, parent in enumerate(cells):
            err = average_error if condition == "neutral_tagged_fission" else errors[i]
            mass = parent.mass + intake[i] - maintenance - error_cost * err
            if mass <= 0.0:
                step_deaths += 1
                continue

            lineage = [Cell(parent.source, mass)]
            j = 0
            while j < len(lineage):
                cell = lineage[j]
                if cell.mass >= 2.0:
                    daughter_mass = cell.mass / 2.0
                    cell.mass = daughter_mass
                    daughter_source = cell.source
                    if condition in {"selected_tagged_fission", "neutral_tagged_fission"}:
                        # The daughter inherits the structural label of the
                        # latest resource packet delivered to this process.
                        label = last_packet_label[i]
                        if label is not None:
                            daughter_source = label
                            step_variants += int(label != cell.source)
                    elif condition == "selected_untyped_fission":
                        # Same uniform genotype law as a random tagged packet,
                        # but the identity is independent of incoming mass.
                        daughter_source = untyped_rng.randrange(source_count)
                        step_variants += int(daughter_source != cell.source)
                    lineage.append(Cell(daughter_source, daughter_mass))
                    step_births += 1
                j += 1
            survivors.extend(lineage)

        cells = survivors
        births += step_births
        deaths += step_deaths
        variant_daughters += step_variants
        packet_total += count
        if not cells and extinct_at is None:
            extinct_at = t + 1

        if t % 20 == 19 or t == steps - 1:
            edge_counts = [sum(cell.source == s for cell in cells)
                           for s in range(source_count)]
            trace.append({
                "step": t + 1, "phase": phase, "active_source": active_source,
                "population": len(cells), "connection_instances": len(cells),
                "distinct_connections": sum(c > 0 for c in edge_counts),
                "source_counts": edge_counts,
                "mean_cell_mass": mean(c.mass for c in cells) if cells else 0.0,
                "matching_source_fraction": edge_counts[active_source] / len(cells) if cells else 0.0,
                "population_target_mse": mean(errors) if errors else 0.5,
                "births_interval": step_births, "deaths_interval": step_deaths,
                "tagged_variant_daughters_interval": step_variants,
            })

    return {
        "seed": seed, "condition": condition, "steps": steps,
        "segment_length": segment_length, "schedule": list(schedule),
        "source_count": source_count, "initial_sources": list(initial_sources),
        "initial_population": initial_population, "initial_mass": initial_mass,
        "substrate_inflow": substrate_inflow, "maintenance": maintenance,
        "error_cost": error_cost, "flip_probability": flip_probability,
        "final_population": len(cells), "final_distinct_connections": len({c.source for c in cells}),
        "total_births": births, "total_deaths": deaths,
        "packet_total": packet_total, "packet_labels_total": packet_labels_total,
        "tagged_variant_daughters": variant_daughters,
        "variant_daughters_per_birth": variant_daughters / births if births else 0.0,
        "extinct_at_step": extinct_at, "trace": trace,
    }


def measurement(row, low=100, high=300):
    result = []
    for item in row["trace"]:
        start = item["phase"] * row["segment_length"]
        if item["phase"] > 0 and start + low <= item["step"] <= start + high:
            result.append(item)
    return result


def summarize(rows):
    summary = {"runs_per_condition": len({r["seed"] for r in rows}), "conditions": {}}
    for condition in sorted({r["condition"] for r in rows}):
        group = [r for r in rows if r["condition"] == condition]
        vals = [item for row in group for item in measurement(row)]
        phase2 = [item for row in group for item in measurement(row) if item["phase"] == 2]
        returned = [item for row in group for item in row["trace"]
                    if item["phase"] == 3 and 2400 <= item["step"] <= 2600]
        summary["conditions"][condition] = {
            "mean_post_shift_matching_fraction_100_300": mean(x["matching_source_fraction"] for x in vals),
            "mean_post_shift_target_mse_100_300": mean(x["population_target_mse"] for x in vals),
            "new_source_2_share_after_first_shift": mean(
                x["source_counts"][2] / x["population"] if x["population"] else 0.0 for x in phase2),
            "source_0_share_after_return": mean(
                x["source_counts"][0] / x["population"] if x["population"] else 0.0 for x in returned),
            "mean_final_population": mean(r["final_population"] for r in group),
            "mean_births": mean(r["total_births"] for r in group),
            "mean_deaths": mean(r["total_deaths"] for r in group),
            "mean_resource_packets": mean(r["packet_total"] for r in group),
            "mean_variant_daughters_per_birth": mean(r["variant_daughters_per_birth"] for r in group),
            "mean_packet_label_frequencies": [mean(r["packet_labels_total"][s] / r["packet_total"]
                                                     for r in group) for s in range(3)],
            "extinctions": sum(r["extinct_at_step"] is not None for r in group),
        }
    return summary


def paired(rows, a, b):
    by = {(row["seed"], row["condition"]): row for row in rows}
    seeds = sorted({row["seed"] for row in rows})
    out = {}
    for name, metric in (("active_share", "matching_source_fraction"), ("target_mse", "population_target_mse")):
        diffs = [mean(x[metric] for x in measurement(by[(s, a)])) -
                 mean(x[metric] for x in measurement(by[(s, b)])) for s in seeds]
        avg = mean(diffs)
        se = stdev(diffs) / len(diffs) ** 0.5 if len(diffs) > 1 else 0.0
        ci = (avg - 2.04523 * se, avg + 2.04523 * se)
        out[name] = {"mean_a_minus_b": avg, "ci95_paired_t": list(ci),
                     "same_direction": sum(d > 0 if name == "active_share" else d < 0 for d in diffs),
                     "per_seed": diffs}
    return out


def main():
    seeds = list(range(30))
    params = {"steps": 3200, "segment_length": 800, "schedule": [0, 1, 2, 0],
              "source_count": 3, "initial_population": 45, "initial_sources": [0, 1],
              "initial_mass": 1.0, "substrate_inflow": 7.7625, "maintenance": 0.10,
              "error_cost": 0.25, "flip_probability": 0.08, "seeds": seeds,
              "conditions": ["selected_tagged_fission", "neutral_tagged_fission",
                             "selected_untyped_fission", "selected_clonal_fission"],
              "measurement_window_after_shift": [100, 300],
              "packet_type_law": "independent uniform label over candidate source edges"}
    kwargs = {k: params[k] for k in ("steps", "segment_length", "schedule", "source_count",
                                     "initial_population", "initial_sources", "initial_mass",
                                     "substrate_inflow", "maintenance", "error_cost", "flip_probability")}
    rows = [run(seed, condition, **kwargs)
            for seed in seeds for condition in params["conditions"]]
    summary = summarize(rows)
    sensitivities = {}
    for factor in (0.9, 1.1):
        group = [run(seed, condition, **{**kwargs, "substrate_inflow": params["substrate_inflow"] * factor})
                 for seed in range(10) for condition in
                 ("selected_tagged_fission", "neutral_tagged_fission",
                  "selected_untyped_fission")]
        s = summarize(group)
        s["paired_selected_minus_neutral"] = paired(group, "selected_tagged_fission",
                                                     "neutral_tagged_fission")
        s["paired_selected_minus_untyped"] = paired(group, "selected_tagged_fission",
                                                      "selected_untyped_fission")
        for row in group:
            row.pop("trace")
        s["per_seed"] = group
        sensitivities[str(factor)] = s

    result = {"model": "edge variants are carried by typed substrate; no mutation-rate parameter",
              "parameters": params, "summary": summary,
              "paired_selected_minus_neutral": paired(rows, "selected_tagged_fission",
                                                        "neutral_tagged_fission"),
              "paired_selected_minus_untyped": paired(rows, "selected_tagged_fission",
                                                        "selected_untyped_fission"),
              "paired_selected_minus_clonal": paired(rows, "selected_tagged_fission",
                                                       "selected_clonal_fission"),
              "supply_sensitivity": sensitivities, "runs": rows}
    out = Path(__file__).with_name("resource_flux_tagged_fission_results.json")
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"summary": summary,
                      "paired_selected_minus_neutral": result["paired_selected_minus_neutral"],
                      "paired_selected_minus_untyped": result["paired_selected_minus_untyped"],
                      "paired_selected_minus_clonal": result["paired_selected_minus_clonal"],
                      "supply_sensitivity": {k: v["conditions"] for k, v in sensitivities.items()},
                      "output": str(out)}, indent=2))


if __name__ == "__main__":
    main()
