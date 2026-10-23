"""Independent 12-source stress replay for H061 against an EMA-Hebb trace."""
import json
import random
import sys
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from candidates.resource_flow_replicator.principle import System


def run(seed, use_flow, source_count=12, segment_length=80, noise=0.15):
    rng = random.Random(seed ^ 0xE17A)
    corr = [0.0] * source_count
    system = System()
    schedule = (0, 3, 7, 10, 6, 2, 11, 1, 4, 9, 5, 8, 0)
    length = segment_length * len(schedule)
    xs = [[rng.randrange(2) for _ in range(source_count)] for _ in range(length)]
    ys = [0.5]
    for t in range(1, length):
        active = schedule[min(t // segment_length, len(schedule) - 1)]
        ys.append(xs[t - 1][active] ^ int(rng.random() < noise))
    rows = []
    previous_x = None
    for t in range(length - 1):
        phase = t // segment_length
        x = xs[t]
        next_phase = (t + 1) // segment_length
        active = schedule[min(next_phase, len(schedule) - 1)]
        next_y = ys[t + 1]
        input_obs = x + [ys[t]]
        if use_flow:
            prediction = system.step(input_obs)[-1]
            winner = max(range(source_count),
                         key=lambda s: system.mass[s][-1] * abs(system.relations[s][-1]))
        else:
            if previous_x is not None:
                for s, before in enumerate(previous_x):
                    corr[s] = 0.97 * corr[s] + 0.03 * (2 * before - 1) * (2 * ys[t] - 1)
            winner = max(range(source_count), key=lambda s: abs(corr[s]))
            prediction = 0.5 + 0.5 * corr[winner] * (2 * x[winner] - 1)
        if t % 10 == 9:
            rows.append({"phase": next_phase, "correct": float(winner == active),
                         "brier": (prediction - next_y) ** 2})
        previous_x = x
    return rows


def summarize(use_flow):
    rows = [r for seed in range(30) for r in run(seed, use_flow)]
    selected = [r for r in rows if 0 < r["phase"] < 13]
    return {"match": mean(r["correct"] for r in selected),
            "brier": mean(r["brier"] for r in selected)}


def main():
    flow = summarize(True)
    hebb = summarize(False)
    result = {
        "protocol": {"seeds": 30, "sources": 12, "segment_length": 80,
                     "noise": 0.15, "schedule": [0, 3, 7, 10, 6, 2, 11, 1, 4, 9, 5, 8, 0]},
        "flow": flow,
        "hebb": hebb,
        "flow_minus_hebb_match": flow["match"] - hebb["match"],
        "flow_minus_hebb_brier": flow["brier"] - hebb["brier"],
    }
    path = Path(__file__).with_name("h061_12source_replay.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
