"""Registered-style A-B-A test for the error-gated causal-support candidate."""
import importlib.util
import json
import random
import statistics
from pathlib import Path

SEEDS = tuple(range(40))
PHASE = 500
CHANNELS = 4


def load_system():
    path = Path(__file__).parents[2] / ".." / "candidates" / "error_gated_support" / "principle.py"
    spec = importlib.util.spec_from_file_location("candidate", path.resolve())
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.System


def stream(seed, null):
    rng = random.Random(seed)
    rows = []
    for step in range(PHASE * 3):
        source = int(rng.random() < 0.5)
        target = None if null else (0 if step < PHASE or step >= 2 * PHASE else 1)
        values = [int(rng.random() < 0.5) for _ in range(CHANNELS)]
        if target is not None:
            values[target] = source ^ int(target == 1) ^ int(rng.random() < 0.08)
        rows.append(([source] + values[1:], target))
    return rows


def run(seed, null):
    system = load_system()()
    errors = []
    chosen = []
    rows = stream(seed, null)
    for index, (observation, target) in enumerate(rows[:-1]):
        prediction = system.step(observation)
        following, following_target = rows[index + 1]
        errors.append((prediction[following_target] - following[following_target]) ** 2 if following_target is not None else sum((p - y) ** 2 for p, y in zip(prediction, following)) / CHANNELS)
        chosen.append(tuple(system.active))
    first = statistics.mean(errors[PHASE - 80:PHASE])
    returned = statistics.mean(errors[2 * PHASE:2 * PHASE + 80])
    return {"first_error": first, "return_error": returned,
            "delta": returned - first, "null_error": statistics.mean(errors),
            "active_changes": sum(a != b for a, b in zip(chosen, chosen[1:]))}


def main():
    target = [run(seed, False) for seed in SEEDS]
    null = [run(seed, True) for seed in SEEDS]
    return {"experiment": "error-gated causal support A-B-A and null",
            "parameters": {"seeds": list(SEEDS), "phase_steps": PHASE, "channels": CHANNELS},
            "target": {"first_error": statistics.mean(r["first_error"] for r in target),
                       "return_error": statistics.mean(r["return_error"] for r in target),
                       "delta": statistics.mean(r["delta"] for r in target),
                       "faster_fraction": sum(r["delta"] < 0 for r in target) / len(target),
                       "active_changes": statistics.mean(r["active_changes"] for r in target)},
            "null": {"error": statistics.mean(r["null_error"] for r in null),
                     "active_changes": statistics.mean(r["active_changes"] for r in null)}}


if __name__ == "__main__":
    result = main()
    Path(__file__).with_name("error_gated_support_result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
