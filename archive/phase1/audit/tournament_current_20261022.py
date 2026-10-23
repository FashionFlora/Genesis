import copy
import importlib.util
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    "single_support_source_mass": ROOT / "candidates/coactivity_single_support_source_mass/principle.py",
    "flux_scale9": ROOT / "candidates/coactivity_flux_scale9/principle.py",
}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def deep_size(value, seen=None):
    if seen is None:
        seen = set()
    obj_id = id(value)
    if obj_id in seen:
        return 0
    seen.add(obj_id)
    total = sys.getsizeof(value)
    if isinstance(value, dict):
        total += sum(deep_size(k, seen) + deep_size(v, seen) for k, v in value.items())
    elif isinstance(value, (list, tuple, set, frozenset)):
        total += sum(deep_size(item, seen) for item in value)
    elif hasattr(value, "__dict__"):
        total += deep_size(vars(value), seen)
    return total


def stream(width, seed=1103):
    rng = random.Random(seed)
    previous = [rng.randrange(2) for _ in range(width)]
    for phase, active in enumerate((0, 1, 0)):
        for _ in range(180):
            obs = [rng.randrange(2) for _ in range(width)]
            for target in range(width // 2, width):
                source = (active + (target - width // 2)) % (width // 2)
                obs[target] = previous[source] if rng.random() >= 0.08 else 1 - previous[source]
            yield phase, obs
            previous = obs


def return_probe(mod):
    system = mod.System()
    phase_errors = [[], [], []]
    structures = []
    for phase, obs in stream(12):
        pred = system.step(obs)
        err = sum((pred[i] - obs[i]) ** 2 for i in range(6, 12)) / 6
        phase_errors[phase].append(err)
        structures.append(system.structure())
    first = sum(phase_errors[0][-32:]) / 32
    middle = sum(phase_errors[1][-32:]) / 32
    returned = sum(phase_errors[2][-32:]) / 32
    return {
        "first_A_tail_brier": first,
        "B_tail_brier": middle,
        "return_A_tail_brier": returned,
        "return_minus_first": returned - first,
        "final_structure": structures[-1],
    }


def prediction_sanity(mod):
    result = {}
    for label, seed, correlated in (("lagged_correlated", 991, True), ("iid", 1991, False)):
        rng = random.Random(seed)
        observations = [[rng.randrange(2) for _ in range(8)]]
        for _ in range(4000):
            previous = observations[-1]
            current = [rng.randrange(2) for _ in range(8)]
            if correlated:
                current[7] = previous[0] if rng.random() >= 0.1 else 1 - previous[0]
            observations.append(current)
        system = mod.System()
        errors = []
        for index in range(4000):
            prediction = system.step(observations[index])
            errors.append((prediction[7] - observations[index + 1][7]) ** 2)
        result[label] = sum(errors) / len(errors)
        result[label + "_tail"] = sum(errors[-800:]) / 800
    result["lagged_minus_iid_brier"] = result["lagged_correlated"] - result["iid"]
    return result


def scale_probe(mod):
    rows = []
    for width in (8, 16, 32, 64, 128):
        system = mod.System()
        rng = random.Random(7919 + width)
        observations = [[rng.randrange(2) for _ in range(width)] for _ in range(80)]
        start = time.perf_counter()
        for obs in observations:
            system.step(obs)
        elapsed = time.perf_counter() - start
        rows.append({
            "width": width,
            "steps": len(observations),
            "seconds": elapsed,
            "microseconds_per_step": elapsed * 1e6 / len(observations),
            "declared_memory_bytes": system.structure().get("memory_bytes"),
            "deep_state_bytes": deep_size(system),
        })
    return rows


def main():
    report = {"generated_by": str(Path(__file__).relative_to(ROOT)), "candidates": {}}
    for name, path in CASES.items():
        mod = load(path, "audit_" + name)
        report["candidates"][name] = {
            "path": str(path.relative_to(ROOT)),
            "timescale": mod.PARAMS.get("timescale"),
            "prediction_sanity": prediction_sanity(mod),
            "return_probe": return_probe(mod),
            "scaling": scale_probe(mod),
        }
    out = ROOT / "audit/tournament_current_result_20261022.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
