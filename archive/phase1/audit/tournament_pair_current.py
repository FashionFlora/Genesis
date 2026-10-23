"""Fresh pairwise audit of the two leading stream candidates.

The test deliberately varies stream order, width, and timescale.  It checks
the public predictions, the hidden returned-flow symmetry, and structural
interfaces without using the sandbox judge.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "coactivity": ROOT / "candidates/coactivity_single_support_source_mass/principle.py",
    "resource_flow": ROOT / "candidates/resource_flow_memory/principle.py",
}


def load(path: Path, tag: str):
    spec = importlib.util.spec_from_file_location(tag, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def deep_size(value, seen=None):
    seen = set() if seen is None else seen
    if id(value) in seen:
        return 0
    seen.add(id(value))
    size = sys.getsizeof(value)
    if isinstance(value, dict):
        return size + sum(deep_size(k, seen) + deep_size(v, seen) for k, v in value.items())
    if isinstance(value, (list, tuple, set)):
        return size + sum(deep_size(v, seen) for v in value)
    if hasattr(value, "__dict__"):
        return size + deep_size(vars(value), seen)
    return size


def stream(width, steps, seed):
    rng = random.Random(seed)
    rows = []
    for _ in range(steps):
        row = [rng.getrandbits(1) for _ in range(width)]
        # Add several changing lagged relations without exposing labels.
        t = len(rows)
        for target in range(width // 2, width):
            source = (target + t) % (width // 2)
            if t and (t + target) % 3 == 0:
                row[target] = rows[-1][source]
        rows.append(row)
    return rows


def run(width, timescale, seed):
    rows = stream(width, 260, seed)
    systems, outputs, timings = {}, {}, {}
    for name, path in FILES.items():
        module = load(path, f"pair_{name}_{width}_{timescale}_{seed}")
        module.PARAMS["timescale"] = timescale
        system = module.System()
        start = time.perf_counter()
        outputs[name] = [system.step(row) for row in rows]
        timings[name] = (time.perf_counter() - start) / len(rows) * 1e6
        systems[name] = system

    prediction_delta = max(
        abs(a - b)
        for left, right in zip(outputs["coactivity"], outputs["resource_flow"])
        for a, b in zip(left, right)
    )
    target_start = width // 2
    mass_spread = max(
        max(systems["resource_flow"].cells[source][target][1] for source in range(width))
        - min(systems["resource_flow"].cells[source][target][1] for source in range(width))
        for target in range(width)
    )
    same_winners = all(
        max(range(width), key=lambda source: abs(systems["coactivity"].support[source][target]))
        == max(
            range(width),
            key=lambda source: abs(systems["resource_flow"].cells[source][target][0])
            * (1 + systems["resource_flow"].cells[source][target][1]),
        )
        for target in range(width)
    )
    brier = {
        name: sum(
            (outputs[name][i][target] - rows[i + 1][target]) ** 2
            for i in range(len(rows) - 1)
            for target in range(target_start, width)
        )
        / ((len(rows) - 1) * (width - target_start))
        for name in FILES
    }
    return {
        "width": width,
        "timescale": timescale,
        "seed": seed,
        "prediction_delta": prediction_delta,
        "target_mass_spread": mass_spread,
        "same_winners": same_winners,
        "brier": brier,
        "deep_state_bytes": {name: deep_size(system) for name, system in systems.items()},
        "microseconds_per_step": timings,
        "has_act": {name: hasattr(load(path, f"act_{name}_{width}_{seed}" ).System(), "act") for name, path in FILES.items()},
    }


def main():
    rows = [
        run(width, timescale, seed)
        for width in (8, 32, 64, 96)
        for timescale in (1.0, 16.0, 64.0)
        for seed in (17, 20261022)
    ]
    result = {
        "test": "fresh random/lagged public-interface pair audit",
        "rows": rows,
        "max_prediction_delta": max(row["prediction_delta"] for row in rows),
        "max_target_mass_spread": max(row["target_mass_spread"] for row in rows),
        "all_winner_maps_equal": all(row["same_winners"] for row in rows),
        "act_interfaces": sorted({tuple(row["has_act"].items()) for row in rows}),
        "source_sha256": {
            name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in FILES.items()
        },
    }
    out = ROOT / "audit/tournament_pair_current_result.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in result if k != "rows"}, sort_keys=True))


if __name__ == "__main__":
    main()
