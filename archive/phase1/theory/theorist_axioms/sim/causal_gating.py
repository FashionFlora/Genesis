"""Test causal-gated plasticity on a recurrent A-B-A stream.

Persistent model evidence is updated only for the currently active causal
address.  A prediction error gates a short-lived search over alternatives;
inactive models are read but not rewritten.  The test asks whether this
separation gives a genuine return advantage while rejecting a null stream.
"""
import json
import random
import statistics
from pathlib import Path

SEEDS = tuple(range(40))
PHASES = 500
CHANNELS = 4
NOISE = 0.08
RULES = (0, 1)  # copy, invert
ERROR_GATE = 0.18
SUSTAINED = 20


def stream(seed, null=False):
    rng = random.Random(seed)
    rows = []
    for t in range(PHASES * 3):
        x = int(rng.random() < 0.5)
        target = None if null else (0 if t < PHASES or t >= 2 * PHASES else 1)
        ys = [int(rng.random() < 0.5) for _ in range(CHANNELS)]
        if target is not None:
            ys[target] = (x ^ (target == 1)) ^ int(rng.random() < NOISE)
        rows.append((x, ys, target))
    return rows


def p_model(counts, x, rule):
    n, ones = counts[rule][x]
    return (ones + 1.0) / (n + 2.0) if rule == 0 else 1.0 - (ones + 1.0) / (n + 2.0)


def sustained(values, target, start, stop):
    run = 0
    for i in range(start, stop):
        run = run + 1 if values[i] == target else 0
        if run >= SUSTAINED:
            return i - start - SUSTAINED + 1
    return stop - start


def run(seed, null=False, gated=True):
    rows = stream(seed, null)
    models = [[[ [0, 0] for _ in (0, 1)] for _ in RULES]
              for _ in range(CHANNELS)]
    quality = [[[0.0, 0.0] for _ in RULES] for _ in range(CHANNELS)]
    # Each [n, ones] pair is local evidence for (channel, rule, source bit).
    # Start on an unrelated address so first acquisition measures discovery.
    active = (2, 1)
    active_errors = 0
    cursor = 0
    choice = []
    losses = []
    for x, ys, target in rows:
        channel, rule = active
        pred = p_model(models[channel], x, rule)
        y = ys[channel]
        loss = (pred - y) ** 2
        losses.append(loss)
        choice.append(channel)
        cell = models[channel][rule][x]
        cell[0] += 1
        cell[1] += y if rule == 0 else 1 - y
        quality[channel][rule][0] += 1.0
        quality[channel][rule][1] += float(loss <= ERROR_GATE)

        active_errors = active_errors + 1 if loss > ERROR_GATE else 0
        if gated and active_errors >= 5:
            # A sustained causal error opens one exploratory contact.  The
            # persistent quality of dormant contacts selects the next address;
            # ties advance a local cursor so unseen alternatives are tried.
            candidates = []
            total = CHANNELS * len(RULES)
            for offset in range(1, total + 1):
                index = (cursor + offset) % total
                c, r = divmod(index, len(RULES))
                seen = quality[c][r][0]
                correct = quality[c][r][1]
                score = correct / seen if seen else 0.5
                candidates.append((score, -offset, c, r))
            _, _, active_channel, active_rule = max(candidates)
            active = (active_channel, active_rule)
            cursor = active_channel * len(RULES) + active_rule
            active_errors = 0
    return {
        "first": sustained(choice, 0, 0, PHASES),
        "return": sustained(choice, 0, 2 * PHASES, 3 * PHASES),
        "brier": statistics.mean(losses),
        "return_occupancy": statistics.mean(v == 0 for v in choice[2 * PHASES:]),
    }


def summary(rows, key):
    vals = [row[key] for row in rows]
    return {"mean": statistics.mean(vals), "sd": statistics.pstdev(vals)}


def main():
    gated = [run(seed) for seed in SEEDS]
    null = [run(seed, True) for seed in SEEDS]
    result = {
        "experiment": "causal-gated plasticity: inactive predictive addresses are conserved",
        "principle": "prediction error gates exploration; only the active causal address is plastic",
        "parameters": {"seeds": list(SEEDS), "phases": PHASES, "channels": CHANNELS,
                       "noise": NOISE, "error_gate": ERROR_GATE, "sustained_steps": SUSTAINED},
        "gated": {key: summary(gated, key) for key in ("first", "return", "brier", "return_occupancy")},
        "return_minus_first": summary([{"v": r["return"] - r["first"]} for r in gated], "v"),
        "return_faster_fraction": statistics.mean(r["return"] < r["first"] for r in gated),
        "null": {key: summary(null, key) for key in ("brier", "return_occupancy")},
    }
    output = Path(__file__).with_name("causal_gating_result.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
