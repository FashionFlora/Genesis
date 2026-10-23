"""Context-addressed prediction and uncertainty-seeking interventions."""
import json
import random
import statistics
from pathlib import Path

SEEDS = tuple(range(40))
PHASE = 600
WINDOW = 40
NOISE = 0.08
ACTIONS = 2


def stream(seed, null=False):
    rng = random.Random(seed)
    for context in (0, 1, 0):
        for _ in range(PHASE):
            cue = rng.randrange(2)
            action = rng.randrange(ACTIONS)
            expected = cue ^ action ^ context
            outcome = rng.random() < (0.5 if null else (1.0 - NOISE if expected else NOISE))
            yield context, action, cue, float(outcome)


class Table:
    def __init__(self, mode):
        self.mode = mode
        self.good = {}
        self.total = {}

    def key(self, row):
        context, action, cue, _ = row
        if self.mode == "context_action":
            return context, action, cue
        if self.mode == "context":
            return context, cue
        return cue,

    def probability(self, row):
        key = self.key(row)
        return (self.good.get(key, 0.5) + 0.5) / (self.total.get(key, 0.0) + 1.0)

    def observe(self, row):
        key = self.key(row)
        self.good[key] = self.good.get(key, 0.5) + row[3]
        self.total[key] = self.total.get(key, 0.0) + 1.0


def run(seed, mode, null=False):
    rows = list(stream(seed, null))
    table = Table(mode)
    errors = []
    for row in rows:
        errors.append((table.probability(row) - row[3]) ** 2)
        table.observe(row)
    return {"mse": statistics.mean(errors), "first_A": statistics.mean(errors[:WINDOW]),
            "return_A": statistics.mean(errors[2 * PHASE:2 * PHASE + WINDOW]),
            "cells": len(table.total)}


def active_intervention(seed):
    """Choose the least observed action, the count-only uncertainty law."""
    rng = random.Random(seed)
    counts = [0] * ACTIONS
    errors = []
    for context in (0, 1, 0):
        for _ in range(PHASE):
            cue = rng.randrange(2)
            action = min(range(ACTIONS), key=counts.__getitem__)
            expected = cue ^ action ^ context
            outcome = float(rng.random() < (1.0 - NOISE if expected else NOISE))
            errors.append((outcome - 0.5) ** 2)
            counts[action] += 1
    return {"balanced_actions": min(counts) / max(counts),
            "return_window_error": statistics.mean(errors[2 * PHASE:2 * PHASE + WINDOW])}


def summarize(items):
    return {key: statistics.mean(item[key] for item in items) for key in items[0]}


def main():
    models = {mode: summarize([run(seed, mode) for seed in SEEDS])
              for mode in ("pooled", "context", "context_action")}
    null = summarize([run(seed, "context_action", True) for seed in SEEDS])
    interventions = summarize([active_intervention(seed) for seed in SEEDS])
    result = {"models": models, "null_context_action": null,
              "intervention": interventions,
              "parameters": {"seeds": len(SEEDS), "phase": PHASE, "noise": NOISE}}
    path = Path(__file__).with_name("contextual_intervention_result.json")
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
