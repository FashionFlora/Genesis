"""A-B-A return test without a phase or context channel."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "candidates/coactivity_total_evidence9/principle.py"
spec = importlib.util.spec_from_file_location("candidate", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def stream(seed):
    state = seed
    for phase, source in enumerate((0, 1, 0)):
        for _ in range(240):
            values = []
            for _ in range(3):
                state = (1103515245 * state + 12345) % (1 << 31)
                values.append((state >> 8) & 1)
            flip = values[2] % 32 == 0
            yield [values[0], values[1], values[0] ^ values[1],
                   values[source] ^ flip], phase


def run(seed):
    system = module.System()
    errors = {0: [], 1: [], 2: []}
    for obs, phase in stream(seed):
        prediction = system.step(obs)
        errors[phase].append((prediction[3] - obs[3]) ** 2)
    return {key: sum(value[-32:]) / 32 for key, value in errors.items()}


rows = [run(seed) for seed in range(12)]
result = {
    "candidate": str(SOURCE.relative_to(ROOT)),
    "seeds": len(rows),
    "first_a_mse": sum(row[0] for row in rows) / len(rows),
    "b_mse": sum(row[1] for row in rows) / len(rows),
    "return_a_mse": sum(row[2] for row in rows) / len(rows),
    "return_minus_first": sum(row[2] - row[0] for row in rows) / len(rows),
}
Path(__file__).with_name("total_evidence_return_result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
