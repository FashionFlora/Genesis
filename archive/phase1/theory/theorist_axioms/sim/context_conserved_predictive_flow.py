"""Paired A-B-A and null test for context-conserved predictive flow."""
import importlib.util
import json
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "candidates/context_conserved_predictive_flow/principle.py"
spec = importlib.util.spec_from_file_location("candidate", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
PHASE = 500
SEEDS = tuple(range(40))


def stream(seed, null=False):
    rng = random.Random(seed)
    for index in range(PHASE * 3):
        phase = index // PHASE
        context = (0, 1, 0)[phase]
        source = int(rng.random() < 0.5)
        values = [context, source] + [int(rng.random() < 0.5) for _ in range(4)]
        if not null:
            values[5] = source if context == 0 else values[3]
            if rng.random() < 0.08:
                values[5] = 1 - values[5]
        yield values


def run(seed, null=False):
    system = module.System()
    errors = []
    for obs in stream(seed, null):
        pred = system.step(obs)
        errors.append((pred[5] - obs[5]) ** 2)
    return statistics.mean(errors[PHASE - 80:PHASE]), statistics.mean(errors[2 * PHASE:2 * PHASE + 80])


target = [run(seed) for seed in SEEDS]
null = [run(seed, True) for seed in SEEDS]
result = {
    "candidate": str(SOURCE.relative_to(ROOT)), "seeds": len(SEEDS), "phase_steps": PHASE,
    "target": {"first_error": statistics.mean(row[0] for row in target),
               "return_error": statistics.mean(row[1] for row in target),
               "return_minus_first": statistics.mean(row[1] - row[0] for row in target),
               "faster_fraction": sum(row[1] < row[0] for row in target) / len(target)},
    "null": {"first_error": statistics.mean(row[0] for row in null),
             "return_error": statistics.mean(row[1] for row in null)},
    "paired_gain_vs_null": statistics.mean((a[0] - a[1]) - (b[0] - b[1])
                                            for a, b in zip(target, null)),
}
Path(__file__).with_name("context_conserved_predictive_flow_result.json").write_text(
    json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
