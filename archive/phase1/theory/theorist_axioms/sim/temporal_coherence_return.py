"""Paired A-B-A return test for temporal coherence closure."""
import importlib.util
import json
import random
import statistics
from pathlib import Path

SEEDS = tuple(range(40))
PHASE = 500
CHANNELS = 4


def system():
    path = Path(__file__).parents[2] / ".." / "candidates" / "temporal_coherence_closure" / "principle.py"
    spec = importlib.util.spec_from_file_location("candidate", path.resolve())
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.System()


def rows(seed, null):
    rng = random.Random(seed); out = []; previous = 0
    for step in range(PHASE * 3):
        source = int(rng.random() < 0.5)
        values = [int(rng.random() < 0.5) for _ in range(CHANNELS)]
        target = None if null else (1 if step < PHASE or step >= 2 * PHASE else 2)
        if target is not None:
            values[target] = previous ^ int(target == 1) ^ int(rng.random() < 0.08)
        out.append(([source] + values[1:], target))
        previous = source
    return out


def run(seed, null=False):
    world = rows(seed, null); learner = system(); errors = []
    for index, (observation, target) in enumerate(world[:-1]):
        prediction = learner.step(observation); following, next_target = world[index + 1]
        errors.append((prediction[next_target] - following[next_target]) ** 2 if next_target is not None else statistics.mean((p - y) ** 2 for p, y in zip(prediction, following)))
    return statistics.mean(errors[PHASE - 80:PHASE]), statistics.mean(errors[2 * PHASE:2 * PHASE + 80]), statistics.mean(errors)


def main():
    target = [run(seed) for seed in SEEDS]; null = [run(seed, True) for seed in SEEDS]
    first = statistics.mean(row[0] for row in target); returned = statistics.mean(row[1] for row in target)
    result = {"seeds": len(SEEDS), "phase": PHASE, "first_error": first, "return_error": returned,
              "return_minus_first": returned - first, "null_error": statistics.mean(row[2] for row in null),
              "null_matched_gain": statistics.mean(row[2] for row in null) - first,
              "faster_fraction": sum(row[1] < row[0] for row in target) / len(target)}
    Path(__file__).with_name("temporal_coherence_return_result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
