"""Compare ecological source discovery with neutral flow and a Hebbian trace."""
from __future__ import annotations

import json
import random
from pathlib import Path
from statistics import mean

from resource_flux_ancestry import run


def hebbian(seed, steps, segment_length, schedule, source_count, timescale):
    rng = random.Random(seed ^ 0xE17A)
    counts = [[0.0, 0.0] for _ in range(source_count)]
    decay = timescale / (timescale + 1.0)
    rows = []
    for t in range(steps):
        phase = min(t // segment_length, len(schedule) - 1)
        active = schedule[phase]
        x = [rng.randrange(2) for _ in range(source_count)]
        y = x[active] ^ int(rng.random() < 0.08)
        estimates = [(pair[1] + 1.0) / (sum(pair) + 2.0)
                     for pair in counts]
        winner = max(range(source_count),
                     key=lambda source: abs(estimates[source] - 0.5))
        for source, bit in enumerate(x):
            counts[source][0] *= decay
            counts[source][1] *= decay
            counts[source][bit] += float(y == 1)
        if t % 10 == 9:
            rows.append((phase, t + 1, float(winner == active)))
    return rows


def main():
    source_count = 12
    schedule = (0, 3, 7, 11)
    segment_length = 250
    steps = segment_length * len(schedule)
    seeds = 8
    windows = {}
    hebb_rows = []
    for seed in range(seeds):
        for condition in ("selected_fission_variation", "neutral_random_fission"):
            result = run(seed, condition, steps=steps,
                         segment_length=segment_length, schedule=schedule,
                         source_count=source_count, initial_population=48,
                         initial_sources=(0, 1), substrate_inflow=7.7625)
            rows = [row for row in result["trace"] if row["phase"] > 0
                    and row["phase"] * segment_length + 50 <= row["step"]
                    <= row["phase"] * segment_length + 200]
            key = "selected" if condition == "selected_fission_variation" else "neutral"
            windows.setdefault(key, []).append({
                "seed": seed,
                "matching_source_fraction": mean(row["matching_source_fraction"]
                                                 for row in rows),
                "target_mse": mean(row["population_target_mse"] for row in rows),
            })
        trace = hebbian(seed, steps, segment_length, schedule, source_count,
                        timescale=33.3333333333)
        observations = [correct for phase, step, correct in trace
                        if phase > 0 and phase * segment_length + 50 <= step
                        <= phase * segment_length + 200]
        hebb_rows.append({"seed": seed,
                          "matching_source_fraction": mean(observations)})
    windows["hebb"] = hebb_rows
    summary = {
        condition: {
            "matching_source_fraction": mean(
                row["matching_source_fraction"] for row in rows),
            "target_mse": mean(row["target_mse"] for row in rows)
            if "target_mse" in rows[0] else None,
        }
        for condition, rows in windows.items()
    }
    summary["paired_selected_minus_neutral_share"] = mean(
        a["matching_source_fraction"] - b["matching_source_fraction"]
        for a, b in zip(windows["selected"], windows["neutral"]))
    result = {
        "world": {"source_count": source_count, "schedule": list(schedule),
                  "segment_length": segment_length, "steps": steps,
                  "seeds": seeds, "measurement_window": [50, 200]},
        "summary": summary,
        "per_seed": windows,
    }
    output = Path(__file__).with_name("resource_flux_scaling_results.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
