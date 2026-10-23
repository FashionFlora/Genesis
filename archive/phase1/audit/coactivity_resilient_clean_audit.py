"""Pair audit for the two current coactivity leaderboard candidates.

This is an audit diagnostic, not a judge replacement: it checks nominal
behavior, state growth, and whether the reported structure identifies edges.
"""

import importlib.util
import json
import random
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATHS = {
    "coactivity_support_resilient": ROOT / "candidates/coactivity_support_resilient/principle.py",
    "coactivity_support_clean": ROOT / "candidates/coactivity_support_clean/principle.py",
}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def deep_size(value, seen=None):
    if seen is None:
        seen = set()
    identity = id(value)
    if identity in seen:
        return 0
    seen.add(identity)
    size = sys.getsizeof(value)
    if isinstance(value, dict):
        size += sum(deep_size(k, seen) + deep_size(v, seen)
                    for k, v in value.items())
    elif isinstance(value, (list, tuple, set)):
        size += sum(deep_size(item, seen) for item in value)
    elif hasattr(value, "__dict__"):
        size += deep_size(vars(value), seen)
    return size


def winner_map(agent):
    """Recover the selected source per target from the full count tensor."""
    result = []
    for target in range(agent.width):
        def gap(source):
            cell = agent.counts[source][target]
            return abs((cell[1][1] + 1.0) / (cell[1][0] + 2.0)
                       - (cell[0][1] + 1.0) / (cell[0][0] + 2.0))
        result.append(max(range(agent.width), key=gap))
    return result


def run_width(width, steps=160):
    modules = {name: load(path, "audit_%s_%d" % (name, width))
               for name, path in PATHS.items()}
    agents = {name: module.System() for name, module in modules.items()}
    rng = random.Random(1811 + width)
    observations = [[rng.getrandbits(1) for _ in range(width)]
                    for _ in range(steps)]
    predictions = {}
    elapsed = {}
    for name, agent in agents.items():
        start = time.perf_counter()
        values = []
        for observation in observations:
            values.append(agent.step(observation))
        elapsed[name] = time.perf_counter() - start
        predictions[name] = values
    mismatches = sum(
        any(abs(a - b) > 1.0e-12 for a, b in zip(predictions["coactivity_support_resilient"][i],
                                                   predictions["coactivity_support_clean"][i]))
        for i in range(steps)
    )
    report = {}
    for name, agent in agents.items():
        report[name] = {
            "elapsed_seconds": elapsed[name],
            "reported_structure": agent.structure(),
            "deep_python_state_bytes": deep_size(vars(agent)),
            "winner_count": len(set(winner_map(agent))),
            "winner_map": winner_map(agent),
            "dense_cells": len(agent.counts) * len(agent.counts[0])
            if agent.counts else 0,
        }
    return {"width": width, "steps": steps,
            "prediction_mismatch_steps": mismatches, "candidates": report}


def main():
    resilient = load(PATHS["coactivity_support_resilient"], "audit_resilient_decay")
    clean = load(PATHS["coactivity_support_clean"], "audit_clean_decay")
    decay_resilient = resilient.PARAMS["timescale"] / (resilient.PARAMS["timescale"] + 1.0)
    decay_clean = min(clean.PARAMS["decay"], 1.0)
    widths = [8, 16, 32, 64]
    rows = [run_width(width) for width in widths]
    payload = {
        "protocol": "160 shared seeded Bernoulli observations at widths 8/16/32/64; no judge calls",
        "decay": {"resilient": decay_resilient, "clean": decay_clean,
                  "absolute_difference": abs(decay_resilient - decay_clean)},
        "rows": rows,
        "interpretation": {
            "nominal_equivalence": "zero prediction mismatches means the tested implementations are behaviorally equivalent on these inputs, not that the principles are independently novel",
            "structure_limit": "both report fixed units and a scalar cross-half edge count while retaining a dense source-target conditional table; winner_map is not returned by structure()",
            "scaling": "dense cell count and measured work grow quadratically with width in this implementation",
        },
    }
    out = ROOT / "audit/coactivity_resilient_clean_audit_result_current.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(out)
    print(json.dumps(payload, separators=(",", ":")))


if __name__ == "__main__":
    main()
