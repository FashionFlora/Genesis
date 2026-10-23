"""Registered parameter sweep for predictive-gated exchange."""
import importlib.util
import json
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "candidates/reversible_predictive_exchange/principle.py"
spec = importlib.util.spec_from_file_location("candidate", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
PHASE = 500


def run(seed, decay, margin):
    module.PARAMS.update(decay=decay, margin=margin)
    rng = random.Random(seed)
    previous_source = int(rng.random() < 0.5)
    observations = []
    for index in range(3 * PHASE + 1):
        source = int(rng.random() < 0.5)
        values = [int(rng.random() < 0.5) for _ in range(4)]
        target = 1 if index < PHASE or index >= 2 * PHASE else 2
        values[target] = previous_source ^ int(target == 2) ^ int(rng.random() < 0.08)
        observations.append(([source] + values[1:], target))
        previous_source = source
    system = module.System()
    errors = []
    for index, (observation, target) in enumerate(observations[:-1]):
        prediction = system.step(observation)
        errors.append((prediction[target] - observations[index + 1][0][target]) ** 2)
    first = statistics.mean(errors[PHASE - 80:PHASE])
    returned = statistics.mean(errors[2 * PHASE:2 * PHASE + 80])
    return first, returned


rows = []
for decay in (0.5, 0.8, 0.95):
    for margin in (0.0, 0.01, 0.05):
        values = [run(seed, decay, margin) for seed in range(40)]
        rows.append({"decay": decay, "margin": margin,
                     "first": statistics.mean(row[0] for row in values),
                     "return": statistics.mean(row[1] for row in values),
                     "return_minus_first": statistics.mean(row[1] - row[0] for row in values)})
result = {"candidate": str(SOURCE.relative_to(ROOT)), "seeds": 40, "rows": rows}
Path(__file__).with_name("reversible_predictive_exchange_sweep_result.json").write_text(
    json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
