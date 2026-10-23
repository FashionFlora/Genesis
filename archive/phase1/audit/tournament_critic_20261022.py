"""Independent critic probe for the source-mass versus resource-flow pair."""
import importlib.util
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = {
    "coactivity": ROOT / "candidates/coactivity_single_support_source_mass/principle.py",
    "resource_flow": ROOT / "candidates/resource_flow_memory/principle.py",
}


def load(path, tag):
    spec = importlib.util.spec_from_file_location(tag, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def deep_size(value, seen=None):
    seen = set() if seen is None else seen
    if id(value) in seen:
        return 0
    seen.add(id(value))
    size = sys.getsizeof(value)
    if isinstance(value, dict):
        size += sum(deep_size(k, seen) + deep_size(v, seen) for k, v in value.items())
    elif isinstance(value, (list, tuple, set)):
        size += sum(deep_size(v, seen) for v in value)
    elif hasattr(value, "__dict__"):
        size += deep_size(vars(value), seen)
    return size


def stream(width, steps, seed, lagged):
    rng = random.Random(seed)
    rows = [[rng.getrandbits(1) for _ in range(width)]]
    for t in range(steps):
        row = [rng.getrandbits(1) for _ in range(width)]
        target = width // 2 + (t % (width - width // 2))
        source = t % (width // 2)
        if lagged:
            row[target] = rows[-1][source]
        rows.append(row)
    return rows


def run(width, timescale, lagged):
    rows = stream(width, 240, 20261022 + width + int(timescale), lagged)
    systems = {}
    outputs = {}
    timings = {}
    for name, path in PATHS.items():
        module = load(path, "critic_%s_%s_%s" % (name, width, timescale))
        module.PARAMS["timescale"] = timescale
        system = module.System()
        start = time.perf_counter()
        outputs[name] = [system.step(row) for row in rows]
        timings[name] = (time.perf_counter() - start) / len(rows) * 1e6
        systems[name] = system
    delta = max(abs(a - b) for left, right in zip(outputs["coactivity"], outputs["resource_flow"])
                for a, b in zip(left, right))
    mass_spread = max(
        max(system.cells[source][target][1] for source in range(width))
        - min(system.cells[source][target][1] for source in range(width))
        for target in range(width)
    )
    # The public step returns a prediction for the next observation: compare
    # its target half with the following row, as the judge's stream contract does.
    brier = {}
    target_start = width // 2
    for name in PATHS:
        brier[name] = sum(
            (outputs[name][index][target] - rows[index + 1][target]) ** 2
            for index in range(len(rows) - 1)
            for target in range(target_start, width)
        ) / (target_start * (len(rows) - 1))
    return {
        "width": width,
        "timescale": timescale,
        "lagged": lagged,
        "max_prediction_delta": delta,
        "max_within_target_mass_spread": mass_spread,
        "brier": brier,
        "deep_state_bytes": {name: deep_size(system) for name, system in systems.items()},
        "microseconds_per_step": timings,
    }


def main():
    rows = [run(width, timescale, lagged)
            for width in (8, 32, 64)
            for timescale in (1.0, 16.0, 64.0)
            for lagged in (True, False)]
    result = {
        "test": "independent public-interface equivalence, mass symmetry, lagged versus IID control",
        "rows": rows,
        "max_delta": max(r["max_prediction_delta"] for r in rows),
        "max_mass_spread": max(r["max_within_target_mass_spread"] for r in rows),
    }
    out = ROOT / "audit/tournament_critic_20261022_result.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
