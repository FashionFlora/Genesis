"""A-B-A and null diagnostic for reversible surprise switching."""
import importlib.util
import json
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "candidates/reversible_surprise/principle.py"
spec = importlib.util.spec_from_file_location("candidate", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

PHASE = 500
SEEDS = tuple(range(40))


def stream(seed, null=False):
    rng = random.Random(seed)
    for index in range(PHASE * 3):
        source = int(rng.random() < 0.5)
        values = [int(rng.random() < 0.5) for _ in range(4)]
        target = None if null else (0 if index < PHASE or index >= 2 * PHASE else 1)
        if target is not None:
            values[target] = source ^ int(target == 1) ^ int(rng.random() < 0.08)
        yield [source] + values[1:], target


def run(seed, null=False):
    system = module.System()
    errors = []
    for observation, target in stream(seed, null):
        prediction = system.step(observation)
        if target is None:
            errors.append(statistics.mean(
                (predicted - actual) ** 2
                for predicted, actual in zip(prediction, observation)))
        else:
            errors.append((prediction[target] - observation[target]) ** 2)
    first = statistics.mean(errors[PHASE - 80:PHASE])
    returned = statistics.mean(errors[2 * PHASE:2 * PHASE + 80])
    return first, returned, statistics.mean(errors)


target = [run(seed) for seed in SEEDS]
null = [run(seed, True) for seed in SEEDS]
result = {
    "candidate": str(SOURCE.relative_to(ROOT)),
    "seeds": len(SEEDS),
    "phase_steps": PHASE,
    "target": {
        "first_error": statistics.mean(row[0] for row in target),
        "return_error": statistics.mean(row[1] for row in target),
        "return_minus_first": statistics.mean(row[1] - row[0] for row in target),
        "faster_fraction": sum(row[1] < row[0] for row in target) / len(target),
    },
    "null": {
        "first_error": statistics.mean(row[0] for row in null),
        "return_error": statistics.mean(row[1] for row in null),
        "return_minus_first": statistics.mean(row[1] - row[0] for row in null),
        "faster_fraction": sum(row[1] < row[0] for row in null) / len(null),
        "mean_error": statistics.mean(row[2] for row in null),
    },
    "target_minus_null_return_gain": statistics.mean(
        (a[0] - a[1]) - (b[0] - b[1]) for a, b in zip(target, null)),
}
Path(__file__).with_name("reversible_surprise_return_result.json").write_text(
    json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
