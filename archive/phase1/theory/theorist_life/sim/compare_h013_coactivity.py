"""Stress local resource-like coactivity flow against a Hebbian trace."""
import json
import random
from pathlib import Path
from statistics import mean


def winner(seed, steps, segment_length, schedule, source_count, timescale):
    rng = random.Random(seed ^ 0xE17A)
    trace = [[[0.0, 0.0] for _ in range(2)] for _ in range(source_count)]
    rows = []
    decay = timescale / (timescale + 1.0)
    for t in range(steps):
        phase = min(t // segment_length, len(schedule) - 1)
        active = schedule[phase]
        x = [rng.randrange(2) for _ in range(source_count)]
        y = x[active] ^ int(rng.random() < 0.08)
        gaps = []
        for source in range(source_count):
            cell = trace[source]
            gaps.append(abs((cell[1][1] + 1.0) / (cell[1][0] + 2.0)
                            - (cell[0][1] + 1.0) / (cell[0][0] + 2.0)))
        choice = max(range(source_count), key=lambda source: gaps[source])
        if t % 20 == 19 or t == steps - 1:
            rows.append({"step": t + 1, "phase": phase, "active": active,
                         "winner": choice, "correct": float(choice == active)})
        for source in range(source_count):
            bit = x[source]
            cell = trace[source][bit]
            for out in range(2):
                cell[out] *= decay
            cell[y] += 1.0
    return rows


def window(rows, phase, segment_length):
    start = phase * segment_length
    return [row for row in rows if row["phase"] == phase
            and start + 100 <= row["step"] <= start + 300]


def main():
    source_count = 12
    segment_length = 800
    schedule = (0, 3, 7, 11, 0)
    steps = segment_length * len(schedule)
    paired = []
    for seed in range(10):
        flow = winner(seed, steps, segment_length, schedule, source_count, 9.0)
        hebb = winner(seed, steps, segment_length, schedule, source_count, 33.333333333333)
        for phase in range(1, len(schedule)):
            flow_rows = window(flow, phase, segment_length)
            hebb_rows = window(hebb, phase, segment_length)
            paired.append({"seed": seed, "phase": phase,
                           "flow_match": mean(row["correct"] for row in flow_rows),
                           "hebb_match": mean(row["correct"] for row in hebb_rows)})
    summary = {key: mean(row[key] for row in paired)
               for key in ("flow_match", "hebb_match")}
    result = {"world": {"sources": source_count, "schedule": list(schedule),
                         "segment_length": segment_length, "seeds": 10,
                         "flow_timescale": 9.0, "hebb_timescale": 33.333333333333},
              "summary": summary, "paired": paired}
    path = Path(__file__).with_name("compare_h013_coactivity_results.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
