"""Test whether context-action indexed predictive state retains causal effects."""
from __future__ import annotations

import json
import random
import statistics
from pathlib import Path


SEEDS = tuple(range(40))
PHASE = 600
WINDOW = 40
NOISE = 0.08


def rows(seed, null=False):
    rng = random.Random(seed)
    data = []
    for phase, context in enumerate((0, 1, 0)):
        for _ in range(PHASE):
            action = rng.randrange(2)
            cue = rng.randrange(2)
            expected = cue ^ action ^ context
            outcome = rng.random() < (0.5 if null else (1.0 - NOISE if expected else NOISE))
            data.append((context, action, cue, float(outcome)))
    return data


class Table:
    def __init__(self, mode):
        self.mode = mode
        self.success = {}
        self.total = {}

    def key(self, context, action, cue):
        if self.mode == "context_action":
            return context, action, cue
        if self.mode == "context_only":
            return context, cue
        if self.mode == "action_only":
            return action, cue
        return cue,

    def predict(self, row):
        context, action, cue, _ = row
        key = self.key(context, action, cue)
        return (self.success.get(key, 0.5) + 0.5) / (self.total.get(key, 0.0) + 1.0)

    def observe(self, row):
        context, action, cue, outcome = row
        key = self.key(context, action, cue)
        self.success[key] = self.success.get(key, 0.5) + outcome
        self.total[key] = self.total.get(key, 0.0) + 1.0


def run(seed, mode, null=False):
    stream = rows(seed, null)
    model = Table(mode)
    errors = []
    for row in stream:
        p = model.predict(row)
        errors.append((p - row[3]) ** 2)
        model.observe(row)
    first = statistics.mean(errors[:WINDOW])
    first_b = statistics.mean(errors[PHASE:PHASE + WINDOW])
    returned = statistics.mean(errors[2 * PHASE:2 * PHASE + WINDOW])
    return {"mse": statistics.mean(errors), "first_A_mse": first,
            "first_B_mse": first_b,
            "return_A_mse": returned, "state_cells": len(model.total)}


def summarize(items):
    return {key: {"mean": statistics.mean(item[key] for item in items),
                  "sd": statistics.stdev(item[key] for item in items)}
            for key in items[0]}


def main():
    modes = ("context_action", "context_only", "action_only", "pooled")
    results = {mode: summarize([run(seed, mode) for seed in SEEDS]) for mode in modes}
    null_results = summarize([run(seed, "context_action", True) for seed in SEEDS])
    data = {"experiment": "context-action indexed predictive sufficiency",
            "parameters": {"seeds": list(SEEDS), "phase_steps": PHASE,
                           "window_steps": WINDOW, "noise": NOISE,
                           "contexts": ["A", "B", "A"],
                           "causal_law": "outcome = cue XOR action XOR context"},
            "models": results, "null_context_action": null_results}
    path = Path(__file__).with_name("action_conditioned_sufficiency_result.json")
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(json.dumps(data, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
