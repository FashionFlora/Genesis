"""Check reversible surprise memory on valid output channels across B gaps."""
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
GAPS = (100, 500, 1500)
SEEDS = tuple(range(40))
WINDOW = 80


def stream(seed, gap, null=False):
    rng = random.Random(seed)
    length = PHASE * 2 + gap
    for index in range(length):
        source = int(rng.random() < 0.5)
        outputs = [int(rng.random() < 0.5) for _ in range(3)]
        if not null:
            if index < PHASE:
                target = 1
            elif index < PHASE + gap:
                target = 2
            else:
                target = 1
            outputs[target - 1] = source ^ int(target == 2) ^ int(rng.random() < 0.08)
        yield [source] + outputs


def run(seed, gap, null=False):
    system = module.System()
    errors = []
    for observation in stream(seed, gap, null):
        prediction = system.step(observation)
        errors.append((prediction[1] - observation[1]) ** 2 if not null else
                      statistics.mean((p - y) ** 2 for p, y in zip(prediction[1:], observation[1:])))
    first = statistics.mean(errors[PHASE - WINDOW:PHASE])
    returned = statistics.mean(errors[PHASE + gap:PHASE + gap + WINDOW])
    return first, returned


def mean(values):
    return statistics.mean(values)


results = {}
for gap in GAPS:
    target = [run(seed, gap) for seed in SEEDS]
    null = [run(seed, gap, True) for seed in SEEDS]
    gains = [(a[0] - a[1]) - (b[0] - b[1]) for a, b in zip(target, null)]
    results[str(gap)] = {
        "target_first_mse": mean([row[0] for row in target]),
        "target_return_mse": mean([row[1] for row in target]),
        "null_first_mse": mean([row[0] for row in null]),
        "null_return_mse": mean([row[1] for row in null]),
        "paired_target_minus_null_gain": mean(gains),
        "positive_seed_fraction": sum(value > 0 for value in gains) / len(gains),
    }

result = {
    "candidate": str(SOURCE.relative_to(ROOT)),
    "seeds": len(SEEDS),
    "A_phase_steps": PHASE,
    "B_gaps": list(GAPS),
    "return_window_steps": WINDOW,
    "target_relation": "source -> output channel 1, then source -> channel 2, then channel 1",
    "results": results,
}
path = Path(__file__).with_name("reversible_surprise_valid_return_sweep_result.json")
path.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
