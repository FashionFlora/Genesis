import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from candidates.inertial_channel_dynamics.principle import System


def run(length=400):
    system = System()
    errors = []
    baseline = []
    for t in range(length):
        value = [float(t % 2)]
        guess = system.step(value)[0]
        if t < length - 1:
            target = float((t + 1) % 2)
            errors.append((guess - target) ** 2)
            baseline.append((0.5 - target) ** 2)
    return {"steps": length - 1,
            "inertial_mse": sum(errors) / len(errors),
            "constant_mse": sum(baseline) / len(baseline),
            "final_inertia": system.inertia[0]}


result = run()
path = Path(__file__).with_name("inertial_channel_toy_result.json")
path.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
