"""Paired fast-switch test of returned local resource against a Hebbian trace."""
import json
import random
from pathlib import Path
from statistics import mean


def run(seed, mode, *, source_count=8, segment_length=80, noise=0.15,
        timescale=16.0):
    rng = random.Random(seed ^ 0xE17A)
    corr = [0.0] * source_count
    mass = [0.0] * source_count
    previous = None
    prediction = 0.5
    schedule = (0, 3, 7, 0, 6, 2, 5, 1, 4, 0)
    rows = []
    for t in range(segment_length * len(schedule)):
        phase = t // segment_length
        active = schedule[phase]
        x = [rng.randrange(2) for _ in range(source_count)]
        y = x[active] ^ int(rng.random() < noise)
        if previous is not None:
            for s, before in enumerate(previous):
                signed = 2.0 * before - 1.0
                target = 2.0 * y - 1.0
                if mode == "flow":
                    local = 0.5 + 0.5 * corr[s] * signed
                    returned = 1.0 / (1.0 + (local - y) ** 2)
                    mass[s] += returned
                    corr[s] = (timescale * corr[s] + signed * target) / (timescale + 1.0)
                else:
                    corr[s] = 0.97 * corr[s] + 0.03 * signed * target
        if mode == "flow":
            winner = max(range(source_count), key=lambda s: mass[s] * abs(corr[s]))
        else:
            winner = max(range(source_count), key=lambda s: abs(corr[s]))
        prediction = 0.5 + 0.5 * corr[winner] * (2.0 * x[winner] - 1.0)
        if t % 10 == 9:
            rows.append({"step": t + 1, "phase": phase, "active": active,
                         "winner": winner, "correct": float(winner == active),
                         "brier": (prediction - y) ** 2})
        previous = x
    return rows


def main():
    rows = []
    for seed in range(30):
        flow = run(seed, "flow")
        hebb = run(seed, "hebb")
        for phase in range(1, 10):
            start = phase * 80
            for mode, trace in (("flow", flow), ("hebb", hebb)):
                window = [r for r in trace if r["phase"] == phase and
                          start + 10 <= r["step"] <= start + 60]
                rows.append({"seed": seed, "phase": phase, "mode": mode,
                             "match": mean(r["correct"] for r in window),
                             "brier": mean(r["brier"] for r in window)})
    summary = {}
    for mode in ("flow", "hebb"):
        selected = [r for r in rows if r["mode"] == mode]
        summary[mode] = {"match": mean(r["match"] for r in selected),
                         "brier": mean(r["brier"] for r in selected)}
    summary["flow_minus_hebb_match"] = summary["flow"]["match"] - summary["hebb"]["match"]
    summary["flow_minus_hebb_brier"] = summary["flow"]["brier"] - summary["hebb"]["brier"]
    output = {"protocol": {"seeds": 30, "sources": 8, "segment_length": 80,
                            "noise": 0.15, "schedule": [0, 3, 7, 0, 6, 2, 5, 1, 4, 0]},
              "summary": summary, "paired": rows}
    path = Path(__file__).with_name("compare_h054_fast_switch_results.json")
    path.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
