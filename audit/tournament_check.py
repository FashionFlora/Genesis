import importlib.util
import json
import random
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(candidate):
    path = ROOT / "candidates" / candidate / "principle.py"
    spec = importlib.util.spec_from_file_location(candidate, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.System()


def run(candidate, widths=(8, 16, 32), steps=30):
    rows = []
    for width in widths:
        system = load(candidate)
        rng = random.Random(1000 + width)
        start = time.perf_counter()
        structures = []
        for _ in range(steps):
            obs = [rng.randrange(2) for _ in range(width)]
            system.step(obs)
            structures.append(system.structure())
        elapsed = time.perf_counter() - start
        rows.append({
            "width": width,
            "seconds": elapsed,
            "first_structure": structures[0],
            "last_structure": structures[-1],
            "units_values": sorted({s.get("units") for s in structures}),
            "connection_values": sorted({s.get("connections") for s in structures}),
        })
    return rows


if __name__ == "__main__":
    print(json.dumps({
        "axiom_predictive_homeostasis": run("axiom_predictive_homeostasis"),
        "coactivity_support": run("coactivity_support"),
    }, sort_keys=True))
