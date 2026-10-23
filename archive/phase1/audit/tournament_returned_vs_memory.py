"""Pairwise public-interface audit of the two resource-flow candidates."""
import importlib.util
import json
import math
import sys
import time


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.System, mod.PARAMS


Returned, returned_params = load(
    "candidates/resource_flow_returned_evidence/principle.py", "returned")
Memory, memory_params = load(
    "candidates/resource_flow_memory/principle.py", "memory")


def stream(width, seed):
    state = seed & 0xFFFFFFFF
    for step in range(80):
        values = []
        for channel in range(width):
            state = (1664525 * state + 1013904223) & 0xFFFFFFFF
            bit = (state >> 31) & 1
            # Mix periodic, correlated, and pseudo-random channels.
            if channel % 5 == 0:
                bit = (step // 3 + channel + seed) & 1
            elif channel % 7 == 0:
                bit ^= (step + seed) & 1
            values.append(bit)
        yield values


def deep_size(obj, seen=None):
    if seen is None:
        seen = set()
    ident = id(obj)
    if ident in seen:
        return 0
    seen.add(ident)
    size = sys.getsizeof(obj)
    if isinstance(obj, dict):
        return size + sum(deep_size(k, seen) + deep_size(v, seen) for k, v in obj.items())
    if isinstance(obj, (list, tuple)):
        return size + sum(deep_size(v, seen) for v in obj)
    return size


def run(system_cls, width, timescale, seed):
    system = system_cls()
    # The candidates expose a module-level parameter dictionary; restore it after each run.
    old = system_cls.__module__
    # The caller sets PARAMS before invoking this function.
    outputs, winners = [], []
    start = time.perf_counter()
    for obs in stream(width, seed):
        outputs.append(system.step(obs))
        if system.cells is not None and system.previous is not None:
            winners.append(tuple(
                max(range(width), key=lambda source: abs(system.cells[source][target][0]))
                for target in range(width)))
    elapsed = time.perf_counter() - start
    return outputs, winners, deep_size(system.__dict__), elapsed


def run_pair(width, timescale, seed):
    returned_params["timescale"] = timescale
    memory_params["timescale"] = timescale
    returned_out, returned_win, returned_mem, returned_time = run(Returned, width, timescale, seed)
    memory_out, memory_win, memory_mem, memory_time = run(Memory, width, timescale, seed)
    max_delta = max(
        abs(a - b)
        for left, right in zip(returned_out, memory_out)
        for a, b in zip(left, right)
    )
    return {
        "width": width,
        "timescale": timescale,
        "seed": seed,
        "max_prediction_delta": max_delta,
        "winner_maps_equal": returned_win == memory_win,
        "returned_memory_bytes": returned_mem,
        "memory_memory_bytes": memory_mem,
        "returned_us_per_step": returned_time * 1e6 / 80,
        "memory_us_per_step": memory_time * 1e6 / 80,
    }


def main():
    runs = [run_pair(width, timescale, seed)
            for width in (8, 32, 64, 96)
            for timescale in (1.0, 16.0, 64.0)
            for seed in (17, 20261023)]
    result = {
        "runs": len(runs),
        "max_prediction_delta": max(r["max_prediction_delta"] for r in runs),
        "all_winner_maps_equal": all(r["winner_maps_equal"] for r in runs),
        "width96_memory_ratio": next(r["memory_memory_bytes"] / r["returned_memory_bytes"]
                                     for r in runs if r["width"] == 96 and r["timescale"] == 16.0 and r["seed"] == 17),
        "width96_returned_us_per_step": next(r["returned_us_per_step"]
                                             for r in runs if r["width"] == 96 and r["timescale"] == 16.0 and r["seed"] == 17),
        "width96_memory_us_per_step": next(r["memory_us_per_step"]
                                            for r in runs if r["width"] == 96 and r["timescale"] == 16.0 and r["seed"] == 17),
        "runs_detail": runs,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    with open("audit/tournament_returned_vs_memory_result.json", "w") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
