"""Paired fast-switch test for the conserved resource-pool principle."""
import importlib.util
import json
import random
from pathlib import Path
from statistics import mean

from compare_h005_hebb import hebb

SPEC = importlib.util.spec_from_file_location(
    "resource_pool", Path(__file__).parents[2] / ".." / "candidates" /
    "resource_pool_return" / "principle.py")
MODEL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODEL)


def flow(seed, source_count=8, segment_length=80, noise=0.15):
    rng = random.Random(seed ^ 0xE17A)
    schedule = (0, 3, 7, 0, 6, 2, 5, 1, 4, 0)
    length = segment_length * len(schedule)
    xs = [[rng.randrange(2) for _ in range(source_count)] for _ in range(length)]
    ys = [0.5]
    for t in range(1, length):
        active = schedule[min(t // segment_length, len(schedule) - 1)]
        ys.append(xs[t - 1][active] ^ int(rng.random() < noise))
    system = MODEL.System()
    rows = []
    for t in range(length - 1):
        system.step(xs[t] + [ys[t]])
        target = schedule[min((t + 1) // segment_length, len(schedule) - 1)]
        winner = max(range(source_count), key=lambda s:
                     system.pool[s][-1] * abs(system.relations[s][-1]))
        prediction = system.prediction[-1]
        if t % 10 == 9:
            rows.append({"phase": (t + 1) // segment_length,
                         "correct": float(winner == target),
                         "brier": (prediction - ys[t + 1]) ** 2})
    return rows


def main():
    schedule = (0, 3, 7, 0, 6, 2, 5, 1, 4, 0)
    rows = []
    for seed in range(30):
        ours = flow(seed)
        baseline = hebb(seed, 800, 80, schedule, 8, 0.15)
        rows.extend((a["correct"], a["brier"], b["correct"], b["brier"])
                    for a, b in zip(ours, baseline)
                    if 0 < a["phase"] < 10)
    summary = {
        "flow_match": mean(row[0] for row in rows),
        "hebb_match": mean(row[2] for row in rows),
        "flow_brier": mean(row[1] for row in rows),
        "hebb_brier": mean(row[3] for row in rows),
    }
    summary["flow_minus_hebb_match"] = summary["flow_match"] - summary["hebb_match"]
    summary["flow_minus_hebb_brier"] = summary["flow_brier"] - summary["hebb_brier"]
    path = Path(__file__).with_name("resource_pool_return_results.json")
    path.write_text(json.dumps({"protocol": {"seeds": 30, "sources": 8,
                                               "segment_length": 80, "noise": 0.15},
                                "summary": summary}, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
