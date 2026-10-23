"""Return-memory diagnostic for consequence_trace_closure."""

import importlib.util
import json
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "candidates/consequence_trace_closure/principle.py"
spec = importlib.util.spec_from_file_location("candidate", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

PHASE = 500
SEEDS = tuple(range(40))


def run(seed, null=False):
    rng = random.Random(seed)
    system = module.System()
    errors = []
    for index in range(PHASE * 3):
        source = rng.randrange(2)
        target = rng.randrange(2)
        regime = None if null else (0 if index < PHASE or index >= 2 * PHASE else 1)
        if regime is not None:
            target = source if regime == 0 else 1 - source
        observation = [source, rng.randrange(2), target]
        prediction = system.step(observation)
        errors.append((prediction[2] - observation[2]) ** 2)
    return (statistics.mean(errors[PHASE - 80:PHASE]),
            statistics.mean(errors[2 * PHASE:2 * PHASE + 80]))


def summarize(rows):
    first = statistics.mean(row[0] for row in rows)
    returned = statistics.mean(row[1] for row in rows)
    return {"first_error": first, "return_error": returned,
            "return_minus_first": returned - first,
            "return_faster_fraction": statistics.mean(row[1] < row[0] for row in rows)}


result = {
    "candidate": str(SOURCE.relative_to(ROOT)),
    "seeds": len(SEEDS),
    "phase_steps": PHASE,
    "target": summarize([run(seed) for seed in SEEDS]),
    "null": summarize([run(seed, True) for seed in SEEDS]),
}
output = Path(__file__).with_name("consequence_trace_return_result.json")
output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
