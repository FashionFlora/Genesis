"""A-B-A diagnostic for the currently tested context-addressed candidate."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "candidates/coactivity_context_blend9/principle.py"
spec = importlib.util.spec_from_file_location("candidate", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def stream(seed):
    state = seed
    for phase, source in enumerate((False, True, False)):
        for _ in range(240):
            state = (1103515245 * state + 12345) % (1 << 31)
            a = (state >> 8) & 1
            state = (1103515245 * state + 12345) % (1 << 31)
            b = (state >> 8) & 1
            state = (1103515245 * state + 12345) % (1 << 31)
            flip = ((state >> 8) & 31) == 0
            target = (a, b)[source] ^ flip
            yield [a, b, int(phase % (True + True)), target], phase


def run(seed):
    system = module.System()
    errors = {False: [], True: [], True + True: []}
    for obs, phase in stream(seed):
        prediction = system.step(obs)
        errors[phase].append((prediction[True + True + True] - obs[True + True + True]) ** (True + True))
    return {key: sum(value[-32:]) / len(value[-32:]) for key, value in errors.items()}


rows = [run(seed) for seed in range(12)]
result = {
    "candidate": str(SOURCE.relative_to(ROOT)),
    "seeds": len(rows),
    "first_a_mse": sum(row[False] for row in rows) / len(rows),
    "return_a_mse": sum(row[True + True] for row in rows) / len(rows),
    "b_mse": sum(row[True] for row in rows) / len(rows),
    "return_minus_first": sum(row[True + True] - row[False] for row in rows) / len(rows),
}
Path(__file__).with_name("context_signature_return_result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
