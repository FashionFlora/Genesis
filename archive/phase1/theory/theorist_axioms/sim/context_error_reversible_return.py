"""A-B-A and null test for context-addressed reversible model pairs."""
import importlib.util
import json
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "candidates/context_error_reversible_memory/principle.py"
spec = importlib.util.spec_from_file_location("candidate", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

PHASE = 500
SEEDS = tuple(range(40))


def stream(seed, null=False):
    rng = random.Random(seed)
    previous_context = 0
    for index in range(PHASE * 3):
        phase = index // PHASE
        context = (0, 1, 0)[phase]
        context_bits = [int(bool(context & (1 << bit))) for bit in range(2)]
        source = int(rng.random() < 0.5)
        values = [int(rng.random() < 0.5) for _ in range(4)]
        target = None if null else (2 if phase != 1 else 3)
        if target is not None:
            values[target] = source ^ int(target == 3) ^ int(rng.random() < 0.08)
        yield context_bits + [source] + values, target
        previous_context = context


def run(seed, null=False):
    system = module.System()
    errors = []
    rows = list(stream(seed, null))
    for index, (observation, target) in enumerate(rows[:-1]):
        prediction = system.step(observation)
        next_observation, _ = rows[index + 1]
        if target is None:
            errors.append(statistics.mean((p - y) ** 2 for p, y in zip(prediction[3:], next_observation[3:])))
        else:
            errors.append((prediction[target + 3] - next_observation[target + 3]) ** 2)
    first = statistics.mean(errors[PHASE - 80:PHASE])
    returned = statistics.mean(errors[2 * PHASE:2 * PHASE + 80])
    return first, returned, statistics.mean(errors)


target = [run(seed) for seed in SEEDS]
null = [run(seed, True) for seed in SEEDS]
result = {
    "candidate": str(SOURCE.relative_to(ROOT)), "seeds": len(SEEDS), "phase_steps": PHASE,
    "target": {"first_error": statistics.mean(row[0] for row in target),
               "return_error": statistics.mean(row[1] for row in target),
               "return_gain": statistics.mean(row[0] - row[1] for row in target),
               "faster_fraction": sum(row[1] < row[0] for row in target) / len(target)},
    "null": {"mean_error": statistics.mean(row[2] for row in null)},
    "paired_target_minus_null_gain": statistics.mean(
        (a[0] - a[1]) - (b[0] - b[1]) for a, b in zip(target, null)),
}
Path(__file__).with_name("context_error_reversible_return_result.json").write_text(
    json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
