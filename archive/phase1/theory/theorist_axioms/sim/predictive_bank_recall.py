"""Test retrieval by the predictive fit of dormant local models."""
import importlib.util
import json
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "candidates/reversible_surprise/principle.py"
spec = importlib.util.spec_from_file_location("baseline", BASE)
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)
CANDIDATE = ROOT / "candidates/predictive_bank_recall/principle.py"
spec = importlib.util.spec_from_file_location("candidate", CANDIDATE)
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)

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
            values[target - 1] = previous_source ^ int(target == 2) ^ int(rng.random() < 0.08)
        yield [source] + values, target
        previous_source = source


def run(seed, system_type, null=False):
    system = system_type()
    errors = []
    for observation, target in stream(seed, null):
        prediction = system.step(observation)
        if target is None:
            errors.append(statistics.mean((p - y) ** 2 for p, y in zip(prediction, observation)))
        else:
            errors.append((prediction[target] - observation[target]) ** 2)
    first = statistics.mean(errors[PHASE - 80:PHASE])
    returned = statistics.mean(errors[2 * PHASE:2 * PHASE + 80])
    return first, returned, statistics.mean(errors)


def summarize(rows):
    return {
        "first_error": statistics.mean(row[0] for row in rows),
        "return_error": statistics.mean(row[1] for row in rows),
        "return_minus_first": statistics.mean(row[1] - row[0] for row in rows),
        "faster_fraction": statistics.mean(row[1] < row[0] for row in rows),
    }


def main():
    recalled = [run(seed, candidate.System) for seed in SEEDS]
    original = [run(seed, baseline.System) for seed in SEEDS]
    null = [run(seed, candidate.System, True) for seed in SEEDS]
    result = {
        "candidate_mechanism": "retrieve the dormant local model with lower current prequential error",
        "seeds": len(SEEDS), "phase_steps": PHASE,
        "recall": summarize(recalled), "original": summarize(original),
        "null_mean_error": statistics.mean(row[2] for row in null),
    }
    path = Path(__file__).with_name("predictive_bank_recall_result.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
