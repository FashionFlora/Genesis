"""Sensory-provenance resource packets as the source of structural growth.

Each ordinary finite resource packet is stamped with the identity of an
currently active sensory input channel (x_s=1). If no input channel is active,
the packet still carries mass but no edge identity. On mass-funded fission,
one daughter inherits its parent's edge and the other incorporates the latest
available sensory-provenance label. Thus candidate edges arise from local
sensory contact at the same event that delivers growth substrate; there is no
independent mutation rate or random alternative-edge operator in the tagged
arm.

The paired untyped control receives the exact same sensory stream, substrate
packet counts, and scalar mass rule, but chooses a uniformly random edge at
fission. A neutral arm uses the same sensory packet labels but spreads the
total prediction-error cost evenly across cells. This tests whether
input-derived structural material adds anything beyond selection and generic
random variation. The provenance-to-edge mapping is an explicit digital
hypothesis, not an established biological fact.
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


def poisson(rng, rate):
    if rate <= 0.0:
        return 0
    threshold, product, count = exp(-rate), 1.0, 0
    while product > threshold:
        count += 1
        product *= rng.random()
    return count - 1


def observation(rng, source_count, active_source, noise):
    x = [rng.randrange(2) for _ in range(source_count)]
    y = x[active_source] ^ int(rng.random() < noise)
    return x, y


def run(seed, condition, *, steps=3200, segment_length=800,
        schedule=(0, 1, 2, 0), source_count=3, initial_population=45,
        initial_sources=(0, 1), initial_mass=1.0, substrate_inflow=7.7625,
        maintenance=0.10, error_cost=0.25, noise=0.08):
    allowed = {"selected_sensory_tag", "neutral_sensory_tag",
               "selected_untyped", "selected_clonal"}
    if condition not in allowed:
        raise ValueError(condition)
    env_rng = random.Random(seed ^ 0xE17A)
    eco_rng = random.Random(seed ^ 0xC011)
    inflow_rng = random.Random(seed ^ 0xF10A)
    route_rng = random.Random(seed ^ 0xA110)
    tag_rng = random.Random(seed ^ 0x1ABE)
    untyped_rng = random.Random(seed ^ 0xA11CE)
    cells = [Cell(initial_sources[i % len(initial_sources)], initial_mass)
             for i in range(initial_population)]
    eco_rng.shuffle(cells)
    trace = []
    births = deaths = packets_total = tagged_packets = variant_daughters = 0
    packet_labels = [0] * source_count
    extinct_at = None

    for t in range(steps):
        phase = min(t // segment_length, len(schedule) - 1)
        active_source = schedule[phase]
        x, y = observation(env_rng, source_count, active_source, noise)
        errors = [float(x[cell.source] != y) for cell in cells]
        mean_error = mean(errors) if errors else 0.5

        n = len(cells)
        count = poisson(inflow_rng, substrate_inflow) if n else 0
        intake = [0] * n
        latest_label = [None] * n
        active_input_labels = [s for s, bit in enumerate(x) if bit == 1]
        for _ in range(count):
            idx = int(route_rng.random() * n)
            intake[idx] += 1
            packets_total += 1
            if active_input_labels:
                label = tag_rng.choice(active_input_labels)
                latest_label[idx] = label
                packet_labels[label] += 1
                tagged_packets += 1

        survivors = []
        step_births = step_deaths = step_variants = 0
        for i, parent in enumerate(cells):
            error = mean_error if condition == "neutral_sensory_tag" else errors[i]
            mass = parent.mass + intake[i] - maintenance - error_cost * error
            if mass <= 0.0:
                step_deaths += 1
                continue
            lineage = [Cell(parent.source, mass)]
            j = 0
            while j < len(lineage):
                cell = lineage[j]
                if cell.mass >= 2.0:
                    child_mass = cell.mass / 2.0
                    cell.mass = child_mass
                    child_source = cell.source
                    if condition in {"selected_sensory_tag", "neutral_sensory_tag"}:
                        if latest_label[i] is not None:
                            child_source = latest_label[i]
                            step_variants += int(child_source != cell.source)
                    elif condition == "selected_untyped":
                        child_source = untyped_rng.randrange(source_count)
                        step_variants += int(child_source != cell.source)
                    lineage.append(Cell(child_source, child_mass))
                    step_births += 1
                j += 1
            survivors.extend(lineage)
        cells = survivors
        births += step_births
        deaths += step_deaths
        variant_daughters += step_variants
        if not cells and extinct_at is None:
            extinct_at = t + 1

        if t % 20 == 19 or t == steps - 1:
            counts = [sum(c.source == s for c in cells) for s in range(source_count)]
            trace.append({
                "step": t + 1, "phase": phase, "active_source": active_source,
                "population": len(cells), "connection_instances": len(cells),
                "distinct_connections": sum(v > 0 for v in counts), "source_counts": counts,
                "mean_cell_mass": mean(c.mass for c in cells) if cells else 0.0,
                "matching_source_fraction": counts[active_source] / len(cells) if cells else 0.0,
                "population_target_mse": mean(errors) if errors else 0.5,
                "births_interval": step_births, "deaths_interval": step_deaths,
                "variants_interval": step_variants,
            })

    return {
        "seed": seed, "condition": condition, "steps": steps,
        "segment_length": segment_length, "schedule": list(schedule),
        "initial_sources": list(initial_sources), "initial_population": initial_population,
        "initial_mass": initial_mass, "substrate_inflow": substrate_inflow,
        "maintenance": maintenance, "error_cost": error_cost, "noise": noise,
        "final_population": len(cells), "final_distinct_connections": len({c.source for c in cells}),
        "total_births": births, "total_deaths": deaths, "total_packets": packets_total,
        "tagged_packets": tagged_packets, "packet_label_counts": packet_labels,
        "packet_label_frequencies": [v / tagged_packets if tagged_packets else 0.0
                                     for v in packet_labels],
        "variant_daughters": variant_daughters,
        "variant_daughters_per_birth": variant_daughters / births if births else 0.0,
        "extinct_at_step": extinct_at, "trace": trace,
    }


def window(row, lo=100, hi=300):
    return [item for item in row["trace"]
            if item["phase"] > 0 and
            item["phase"] * row["segment_length"] + lo <= item["step"] <=
            item["phase"] * row["segment_length"] + hi]


def summarize(rows):
    out = {"runs_per_condition": len({r["seed"] for r in rows}), "conditions": {}}
    for cond in sorted({r["condition"] for r in rows}):
        group = [r for r in rows if r["condition"] == cond]
        measured = [t for r in group for t in window(r)]
        source2 = [t for r in group for t in window(r) if t["phase"] == 2]
        back0 = [t for r in group for t in r["trace"]
                 if t["phase"] == 3 and 2400 <= t["step"] <= 2600]
        out["conditions"][cond] = {
            "active_share": mean(t["matching_source_fraction"] for t in measured),
            "target_mse": mean(t["population_target_mse"] for t in measured),
            "source2_share_after_first_shift": mean(
                t["source_counts"][2] / t["population"] if t["population"] else 0.0
                for t in source2),
            "source0_share_after_return": mean(
                t["source_counts"][0] / t["population"] if t["population"] else 0.0
                for t in back0),
            "mean_final_population": mean(r["final_population"] for r in group),
            "mean_births": mean(r["total_births"] for r in group),
            "mean_deaths": mean(r["total_deaths"] for r in group),
            "mean_variant_fraction": mean(r["variant_daughters_per_birth"] for r in group),
            "mean_packet_label_frequencies": [mean(r["packet_label_frequencies"][i]
                                                      for r in group) for i in range(3)],
            "extinctions": sum(r["extinct_at_step"] is not None for r in group),
        }
    return out


def paired(rows, a, b):
    by = {(r["seed"], r["condition"]): r for r in rows}
    seeds = sorted({r["seed"] for r in rows})
    out = {}
    for metric, key in (("active_share", "matching_source_fraction"), ("target_mse", "population_target_mse")):
        diffs = [mean(x[key] for x in window(by[s, a])) - mean(x[key] for x in window(by[s, b]))
                 for s in seeds]
        avg = mean(diffs)
        se = stdev(diffs) / len(diffs) ** .5
        out[metric] = {"mean_a_minus_b": avg,
                       "ci95_paired_t": [avg - 2.04523 * se, avg + 2.04523 * se],
                       "same_direction": sum(v > 0 if metric == "active_share" else v < 0
                                              for v in diffs),
                       "per_seed": diffs}
    return out


def main():
    seeds = list(range(30))
    params = {"steps": 3200, "segment_length": 800, "schedule": [0, 1, 2, 0],
              "source_count": 3, "initial_population": 45, "initial_sources": [0, 1],
              "initial_mass": 1.0, "substrate_inflow": 7.7625, "maintenance": 0.10,
              "error_cost": 0.25, "noise": 0.08, "seeds": seeds,
              "conditions": ["selected_sensory_tag", "neutral_sensory_tag",
                             "selected_untyped", "selected_clonal"],
              "measurement_window_after_shift": [100, 300],
              "tag_rule": "packet label uniformly samples among sensory channels with x_s=1; all-zero observation yields untyped mass packet"}
    kwargs = {k: params[k] for k in ("steps", "segment_length", "schedule", "source_count",
                                     "initial_population", "initial_sources", "initial_mass",
                                     "substrate_inflow", "maintenance", "error_cost", "noise")}
    rows = [run(seed, cond, **kwargs) for seed in seeds for cond in params["conditions"]]
    summary = summarize(rows)
    sensitivity = {}
    for factor in (0.9, 1.1):
        group = [run(seed, cond, **{**kwargs, "substrate_inflow": params["substrate_inflow"] * factor})
                 for seed in range(10) for cond in
                 ("selected_sensory_tag", "neutral_sensory_tag", "selected_untyped")]
        s = summarize(group)
        s["paired_tagged_minus_neutral"] = paired(group, "selected_sensory_tag", "neutral_sensory_tag")
        s["paired_tagged_minus_untyped"] = paired(group, "selected_sensory_tag", "selected_untyped")
        for row in group:
            row.pop("trace")
        s["per_seed"] = group
        sensitivity[str(factor)] = s
    result = {"model": "sensory-provenance resource packet labels materialize daughter edges",
              "parameters": params, "summary": summary,
              "paired_tagged_minus_neutral": paired(rows, "selected_sensory_tag", "neutral_sensory_tag"),
              "paired_tagged_minus_untyped": paired(rows, "selected_sensory_tag", "selected_untyped"),
              "paired_tagged_minus_clonal": paired(rows, "selected_sensory_tag", "selected_clonal"),
              "supply_sensitivity": sensitivity, "runs": rows}
    out = Path(__file__).with_name("resource_flux_sensory_fission_results.json")
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"summary": summary,
                      "paired_tagged_minus_neutral": result["paired_tagged_minus_neutral"],
                      "paired_tagged_minus_untyped": result["paired_tagged_minus_untyped"],
                      "paired_tagged_minus_clonal": result["paired_tagged_minus_clonal"],
                      "supply_sensitivity": {k: v["conditions"] for k, v in sensitivity.items()},
                      "output": str(out)}, indent=2))


if __name__ == "__main__":
    main()
