"""Compare the public behavior and state cost of two leaderboard candidates."""

import importlib.util
import json
import random
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = {
    "coactivity": ROOT / "candidates/coactivity_single_support_source_mass/principle.py",
    "resource_flow": ROOT / "candidates/resource_flow_memory/principle.py",
}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def deep_size(value, seen=None):
    if seen is None:
        seen = set()
    if id(value) in seen:
        return 0
    seen.add(id(value))
    size = sys.getsizeof(value)
    if isinstance(value, dict):
        size += sum(deep_size(k, seen) + deep_size(v, seen)
                    for k, v in value.items())
    elif isinstance(value, (list, tuple, set)):
        size += sum(deep_size(item, seen) for item in value)
    elif hasattr(value, "__dict__"):
        size += deep_size(vars(value), seen)
    return size


def probe(width, steps, seed):
    rng = random.Random(seed)
    observations = [[rng.getrandbits(1) for _ in range(width)]]
    # Add both stationary and returning regimes without revealing their identity.
    for step in range(steps):
        row = [rng.getrandbits(1) for _ in range(width)]
        source = step % max(1, width // 2)
        target = width // 2 + (step % max(1, width - width // 2))
        row[target] = observations[-1][source] if step % 3 else 1 - observations[-1][source]
        observations.append(row)

    agents = {}
    predictions = {}
    timings = {}
    for name, path in CANDIDATES.items():
        system = load(path, "audit_%s_%d" % (name, width)).System()
        start = time.perf_counter()
        output = [system.step(row) for row in observations[:-1]]
        elapsed = time.perf_counter() - start
        agents[name] = system
        predictions[name] = output
        timings[name] = elapsed / steps * 1e6

    a, b = predictions["coactivity"], predictions["resource_flow"]
    max_prediction_delta = max(abs(x - y) for row_a, row_b in zip(a, b)
                              for x, y in zip(row_a, row_b))
    flow_cells = agents["resource_flow"].cells
    per_target_mass_spread = [
        max(flow_cells[source][target][1] for source in range(width))
        - min(flow_cells[source][target][1] for source in range(width))
        for target in range(width)
    ]
    return {
        "width": width,
        "steps": steps,
        "seed": seed,
        "max_prediction_delta": max_prediction_delta,
        "connection_readout_delta": abs(agents["coactivity"].edges - agents["resource_flow"].edges),
        "connection_readouts_equal_within_1e-12": abs(
            agents["coactivity"].edges - agents["resource_flow"].edges) < 1e-12,
        "max_within_target_mass_spread": max(per_target_mass_spread),
        "deep_state_bytes": {name: deep_size(agent) for name, agent in agents.items()},
        "microseconds_per_step": timings,
    }


def main():
    rows = [probe(width, 160, 20261022 + width) for width in (32, 64, 128)]
    result = {
        "test": "public-interface equivalence, target-mass symmetry, and dense scaling",
        "rows": rows,
        "inference": (
            "Resource-flow mass is uniform across source candidates for each target; "
            "multiplying every candidate support by the same positive target factor "
            "cannot change that target's argmax."
        ),
    }
    out = ROOT / "audit/tournament_resource_vs_coactivity_result.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
