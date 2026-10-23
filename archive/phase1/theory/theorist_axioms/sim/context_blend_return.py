"""Small A-B-A return diagnostic for context-addressed coactivity."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "candidates/coactivity_context_blend/principle.py"
spec = importlib.util.spec_from_file_location("candidate", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def stream(seed):
    state = seed
    for phase, source in enumerate((0, 1, 0)):
        for _ in range(240):
            state = (1103515245 * state + 12345) % (1 << 31)
            a = (state >> 8) & 1
            state = (1103515245 * state + 12345) % (1 << 31)
            b = (state >> 8) & 1
            state = (1103515245 * state + 12345) % (1 << 31)
            flip = ((state >> 8) & 31) == 0
            target = (a, b)[source] ^ flip
            yield [a, b, phase % 2, target], phase


def run(system):
    errors = {0: [], 1: [], 2: []}
    for obs, phase in stream(17):
        prediction = system.step(obs)
        errors[phase].append((prediction[3] - obs[3]) ** 2)
    return {key: sum(value[-32:]) / len(value[-32:]) for key, value in errors.items()}


rows = []
for seed in range(12):
    rows.append(run(module.System()))
result = {
    "seeds": 12,
    "first_a_mse": sum(row[0] for row in rows[:]) / len(rows),
    "return_a_mse": sum(row[2] for row in rows) / len(rows),
    "b_mse": sum(row[1] for row in rows) / len(rows),
    "return_minus_first": sum(row[2] - row[0] for row in rows) / len(rows),
    "note": "Diagnostic uses a phase bit in the context channel; it checks that the harness can expose recurrence, not a world-general claim.",
}
Path(__file__).with_name("context_blend_return_result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
