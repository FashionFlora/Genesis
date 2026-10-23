"""A-B-A and null diagnostic for contextual surprise-regulated traces."""
import importlib.util
import json
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "candidates/contextual_surprise_reserve/principle.py"
spec = importlib.util.spec_from_file_location("candidate", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
PHASE = 500
SEEDS = tuple(range(40))


def stream(seed, null=False):
    rng = random.Random(seed)
    previous_source = int(rng.random() < 0.5)
    for index in range(PHASE * 3):
        source = int(rng.random() < 0.5)
        values = [int(rng.random() < 0.5) for _ in range(4)]
        target = None if null else (1 if index < PHASE or index >= 2 * PHASE else 2)
        if target is not None:
            values[target] = previous_source ^ int(target == 2) ^ int(rng.random() < 0.08)
        yield [source] + values, target
        previous_source = source


def run(seed, null=False):
    system = module.System()
    errors = []
    for observation, target in stream(seed, null):
        prediction = system.step(observation)
        if target is None:
            errors.append(statistics.mean((p - y) ** 2 for p, y in zip(prediction, observation)))
        else:
            errors.append((prediction[target] - observation[target]) ** 2)
    return (statistics.mean(errors[:80]),
            statistics.mean(errors[PHASE - 80:PHASE]),
            statistics.mean(errors[2 * PHASE:2 * PHASE + 80]),
            statistics.mean(errors))


recalled = [run(seed) for seed in SEEDS]
null_rows = [run(seed, True) for seed in SEEDS]
result = {
    "candidate": str(SOURCE.relative_to(ROOT)),
    "seeds": len(SEEDS),
    "phase_steps": PHASE,
    "first_a_mse": statistics.mean(row[0] for row in recalled),
    "late_a_mse": statistics.mean(row[1] for row in recalled),
    "return_a_mse": statistics.mean(row[2] for row in recalled),
    "return_faster_fraction": statistics.mean(row[2] < row[0] for row in recalled),
    "null_mean_mse": statistics.mean(row[3] for row in null_rows),
}
Path(__file__).with_name("contextual_surprise_reserve_return_result.json").write_text(
    json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
