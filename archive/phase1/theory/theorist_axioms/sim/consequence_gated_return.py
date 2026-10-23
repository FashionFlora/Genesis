"""A-B-A test for consequence-gated relational evidence, with a null."""
import importlib.util
import json
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "candidates/consequence_gated_return_flow/principle.py"
spec = importlib.util.spec_from_file_location("candidate", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
PHASE = 500
GAPS = (100, 500, 1500)
SEEDS = tuple(range(40))
WINDOW = 80


def stream(seed, gap, null=False):
    rng = random.Random(seed)
    for index in range(PHASE * 2 + gap):
        source = int(rng.random() < 0.5)
        outputs = [int(rng.random() < 0.5) for _ in range(3)]
        if not null:
            target = 1 if index < PHASE or index >= PHASE + gap else 2
            outputs[target - 1] = source ^ int(target == 2) ^ int(rng.random() < 0.08)
        yield [source] + outputs


def run(seed, gap, null=False):
    system = module.System()
    errors = []
    for observation in stream(seed, gap, null):
        prediction = system.step(observation)
        errors.append((prediction[1] - observation[1]) ** 2 if not null else
                      statistics.mean((p - y) ** 2 for p, y in zip(prediction[1:], observation[1:])))
    return (statistics.mean(errors[PHASE - WINDOW:PHASE]),
            statistics.mean(errors[PHASE + gap:PHASE + gap + WINDOW]))


results = {}
for gap in GAPS:
    target = [run(seed, gap) for seed in SEEDS]
    null = [run(seed, gap, True) for seed in SEEDS]
    gains = [(a[0] - a[1]) - (b[0] - b[1]) for a, b in zip(target, null)]
    results[str(gap)] = {
        "target_first_mse": statistics.mean(row[0] for row in target),
        "target_return_mse": statistics.mean(row[1] for row in target),
        "null_first_mse": statistics.mean(row[0] for row in null),
        "null_return_mse": statistics.mean(row[1] for row in null),
        "paired_target_minus_null_gain": statistics.mean(gains),
        "positive_seed_fraction": sum(value > 0 for value in gains) / len(gains),
    }
result = {"candidate": str(SOURCE.relative_to(ROOT)), "seeds": len(SEEDS),
          "A_phase_steps": PHASE, "B_gaps": list(GAPS),
          "return_window_steps": WINDOW, "results": results}
path = Path(__file__).with_name("consequence_gated_return_result.json")
path.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
