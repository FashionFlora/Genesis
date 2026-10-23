"""Independent-stream falsifier for context-addressed predictive state."""
import importlib.util
import json
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "candidates/contextual_predictive_sufficiency/principle.py"
spec = importlib.util.spec_from_file_location("candidate", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def run(seed):
    rng = random.Random(seed)
    system = module.System()
    losses = []
    errors = []
    for step in range(2400):
        obs = [float(rng.randrange(2)) for _ in range(12)]
        pred = system.step(obs)
        losses.append(statistics.mean((p - y) ** 2 for p, y in zip(pred, obs)))
        errors.append((pred[9] - obs[9]) ** 2)
    structure = system.structure()
    return {"seed": seed, "mse": statistics.mean(losses),
            "tail_mse": statistics.mean(errors[-256:]),
            "units": structure["units"],
            "connections": structure["connections"],
            "memory_bytes": structure["memory_bytes"]}


rows = [run(seed) for seed in range(40, 64)]
result = {
    "candidate": str(SOURCE.relative_to(ROOT)),
    "streams": len(rows),
    "independent_bernoulli_null": {
        key: {"mean": statistics.mean(row[key] for row in rows),
              "sd": statistics.pstdev(row[key] for row in rows)}
        for key in ("mse", "tail_mse", "connections", "memory_bytes")
    },
    "chance_mse": 0.25,
    "rows": rows,
}
out = Path(__file__).with_name("contextual_null_test_result.json")
out.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k != "rows"}, sort_keys=True))
