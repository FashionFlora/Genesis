"""Paired higher-dimensional stress test: typed resource flow vs local Hebb."""
import json
import random
from pathlib import Path
from statistics import mean

from resource_flux_tagged_fission import measurement, run


def hebb(seed, steps, segment_length, schedule, source_count, flip_probability):
    rng = random.Random(seed ^ 0xE17A)
    decay = 0.97
    seen = [[[0.0, 0.0] for _ in range(2)] for _ in range(source_count)]
    yes = [[[0.0, 0.0] for _ in range(2)] for _ in range(source_count)]
    trace = []
    for t in range(steps):
        phase = min(t // segment_length, len(schedule) - 1)
        active = schedule[phase]
        x = [rng.randrange(2) for _ in range(source_count)]
        y = x[active] ^ int(rng.random() < flip_probability)
        gaps = []
        for s in range(source_count):
            p1 = [(yes[s][b][1] + 1) / (seen[s][b][1] + 2) for b in range(2)]
            gaps.append(abs(p1[1] - p1[0]))
        winner = max(range(source_count), key=lambda s: gaps[s])
        if t % 20 == 19 or t == steps - 1:
            trace.append({"step": t + 1, "phase": phase, "active": active,
                          "winner": winner, "correct": float(winner == active)})
        for s in range(source_count):
            b = x[s]
            for out in range(2):
                seen[s][b][out] *= decay
                yes[s][b][out] *= decay
            seen[s][b][y] += 1
            yes[s][b][y] += 1
    return trace


def window(trace, phase, segment_length):
    start = phase * segment_length
    return [row for row in trace if row["phase"] == phase
            and start + 100 <= row["step"] <= start + 300]


def main():
    source_count = 12
    segment_length = 800
    schedule = (0, 3, 7, 11, 0)
    steps = segment_length * len(schedule)
    kwargs = dict(steps=steps, segment_length=segment_length, schedule=schedule,
                  source_count=source_count, initial_population=90,
                  initial_sources=(0, 1, 2), initial_mass=1.0,
                  substrate_inflow=7.7625, maintenance=0.10, error_cost=0.25,
                  flip_probability=0.08)
    paired = []
    for seed in range(10):
        ecological = run(seed, "selected_tagged_fission", **kwargs)
        hebbian = hebb(seed, steps, segment_length, schedule, source_count, 0.08)
        for phase in range(1, len(schedule)):
            ec = [x for x in measurement(ecological, 100, 300) if x["phase"] == phase]
            hb = window(hebbian, phase, segment_length)
            paired.append({"seed": seed, "phase": phase,
                           "resource_match": mean(x["matching_source_fraction"] for x in ec),
                           "resource_mse": mean(x["population_target_mse"] for x in ec),
                           "hebb_match": mean(x["correct"] for x in hb)})
    result = {"world": {"sources": source_count, "schedule": list(schedule),
                         "segment_length": segment_length, "seeds": 10},
              "summary": {key: mean(row[key] for row in paired)
                          for key in ("resource_match", "resource_mse", "hebb_match")},
              "paired": paired}
    path = Path(__file__).with_name("compare_h005_hebb_results.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
