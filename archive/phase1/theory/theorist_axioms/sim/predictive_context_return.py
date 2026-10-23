"""A-B-A return test for predictive-context sufficiency and an independent null."""
import importlib.util
import json
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "candidates/predictive_context_sufficiency/principle.py"
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
            values[3] = source if target == 0 else values[1]
            if rng.random() < 0.08:
                values[3] = 1 - values[3]
        yield [source, values[1], values[2], values[3]]


def run(seed, null=False):
    system = module.System()
    errors = []
    for observation in stream(seed, null):
        prediction = system.step(observation)
        errors.append((prediction[3] - observation[3]) ** 2)
    first = statistics.mean(errors[PHASE - 80:PHASE])
    returned = statistics.mean(errors[2 * PHASE:2 * PHASE + 80])
    return first, returned


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
        "mean_error": statistics.mean(row[1] for row in null),
    },
}
Path(__file__).with_name("predictive_context_return_result.json").write_text(
    json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
