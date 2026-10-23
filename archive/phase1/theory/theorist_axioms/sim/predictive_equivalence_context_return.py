"""Return-memory test with an observable context and a matched null."""
import importlib.util
import json
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "candidates/contextual_predictive_equivalence/principle.py"
spec = importlib.util.spec_from_file_location("candidate", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

PHASE = 800
SEEDS = tuple(range(40))


def run(seed, changed=True):
    rng = random.Random(seed)
    system = module.System()
    errors = []
    for index in range(PHASE * 3):
        phase = index // PHASE
        context = (0, 1, 0)[phase]
        source = int(rng.random() < 0.5)
        target = source ^ int(rng.random() < 0.08) if not changed or context == 0 else int(rng.random() < 0.5)
        observation = [source, int(rng.random() < 0.5), context, target]
        prediction = system.step(observation)
        errors.append((prediction[3] - target) ** 2)
    return (statistics.mean(errors[PHASE - 80:PHASE]),
            statistics.mean(errors[2 * PHASE:2 * PHASE + 80]))


target = [run(seed) for seed in SEEDS]
null = [run(seed, False) for seed in SEEDS]
result = {
    "candidate": str(SOURCE.relative_to(ROOT)),
    "seeds": len(SEEDS),
    "phase_steps": PHASE,
    "target": {
        "first_error": statistics.mean(row[0] for row in target),
        "return_error": statistics.mean(row[1] for row in target),
        "return_minus_first": statistics.mean(row[1] - row[0] for row in target),
        "return_gain_vs_first": statistics.mean(row[0] - row[1] for row in target),
        "faster_fraction": sum(row[1] < row[0] for row in target) / len(target),
    },
    "matched_null": {
        "first_error": statistics.mean(row[0] for row in null),
        "return_error": statistics.mean(row[1] for row in null),
        "return_gain_vs_first": statistics.mean(row[0] - row[1] for row in null),
    },
    "test_headroom": {
        "chance_mse": 0.25,
        "known_a_relation_mse": 0.08,
        "meaning": "Bayes error for the noisy A relation; B is independent fair noise.",
    },
    "paired_gain_over_null": statistics.mean(
        (a[0] - a[1]) - (b[0] - b[1]) for a, b in zip(target, null)),
}
out = Path(__file__).with_name("predictive_equivalence_context_return_result.json")
out.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
