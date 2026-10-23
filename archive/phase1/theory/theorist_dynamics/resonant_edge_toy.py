import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from candidates.resonant_edge_dynamics.principle import System


def run(length=240, warmup=32):
    system = System()
    errors = []
    baseline = []
    for step in range(length):
        phase = step % 2
        observation = [float(phase), float(1 - phase)]
        prediction = system.step(observation)
        if step:
            target = [float(1 - phase), float(phase)]
            errors.append(sum((guess - value) ** 2
                              for guess, value in zip(prediction, target)) / 2.0)
            baseline.append(0.25)
    return {"steps": length - 1,
            "warmup": warmup,
            "all_brier": sum(errors) / len(errors),
            "late_brier": sum(errors[warmup:]) / len(errors[warmup:]),
            "constant_brier": sum(baseline) / len(baseline),
            "connections": system.edges}


result = run()
Path(__file__).with_name("resonant_edge_toy_result.json").write_text(
    json.dumps(result, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
