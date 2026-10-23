"""Return-memory diagnostic for the current contextual model exchange."""
import importlib.util
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "candidates/contextual_reversible_intervention/principle.py"
spec = importlib.util.spec_from_file_location("candidate", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

PHASE = 800
WINDOW = 40


def stream(seed):
    rng = random.Random(seed)
    previous = [rng.randrange(2), rng.randrange(2)]
    for phase, source in enumerate((0, 1, 0)):
        for _ in range(PHASE):
            cue0 = rng.randrange(2)
            cue1 = rng.randrange(2)
            context = phase % 2
            target = previous[source] ^ int(rng.random() < 0.05)
            previous = [cue0, cue1]
            yield [cue0, cue0, cue1, cue1, context, target, target], phase


def run(seed):
    system = module.System()
    errors = {0: [], 1: [], 2: []}
    observations = list(stream(seed))
    for index, (observation, _) in enumerate(observations[:-1]):
        prediction = system.step(observation)
        next_observation, phase = observations[index + 1]
        errors[phase].append((prediction[5] - next_observation[5]) ** 2)
    return {
        "first_a": sum(errors[0][:WINDOW]) / WINDOW,
        "b": sum(errors[1][:WINDOW]) / WINDOW,
        "return_a": sum(errors[2][:WINDOW]) / WINDOW,
        "first_a_late": sum(errors[0][-WINDOW:]) / WINDOW,
    }


rows = [run(seed) for seed in range(40)]
result = {
    "candidate": str(SOURCE.relative_to(ROOT)),
    "seeds": len(rows),
    "phase_steps": PHASE,
    "window_steps": WINDOW,
    "first_a_mse": sum(row["first_a"] for row in rows) / len(rows),
    "b_mse": sum(row["b"] for row in rows) / len(rows),
    "return_a_mse": sum(row["return_a"] for row in rows) / len(rows),
    "return_minus_first": sum(row["return_a"] - row["first_a"] for row in rows) / len(rows),
    "first_a_late_mse": sum(row["first_a_late"] for row in rows) / len(rows),
}
Path(__file__).with_name("contextual_reversible_return_result.json").write_text(
    json.dumps(result, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
