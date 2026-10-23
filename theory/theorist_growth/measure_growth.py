"""Measure the candidate on seeded streams with expanding sparse dependencies."""

import importlib.util
import json
import random
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "growth_principle", ROOT / "candidates/growth_nucleation/principle.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def run(width):
    rng = random.Random(31 + width)
    sources = width // 2
    previous = [float(rng.randrange(2)) for _ in range(width)]
    mapping = [rng.randrange(sources) for _ in range(width - sources)]
    system = MODULE.System()
    phase_rows = []
    step = 0
    for complexity in (1, 2, 4, 8):
        errors = []
        started = time.perf_counter()
        for _ in range(96):
            current = [float(rng.randrange(2)) for _ in range(sources)]
            current += [previous[sources + i] if i >= complexity else
                        float(int(previous[mapping[i]]) ^ int(rng.random() < 0.08))
                        for i in range(width - sources)]
            pred = system.step(previous)
            errors.extend((pred[i] - current[i]) ** 2 for i in range(width))
            previous = current
            step += 1
        structure = system.structure()
        phase_rows.append({"complexity": complexity,
                           "step": step, "brier": sum(errors) / len(errors),
                           "ms_per_step": (time.perf_counter() - started) * 1000 / 96,
                           **structure})
    return {"width": width, "phases": phase_rows}


print(json.dumps({"candidate": "growth_nucleation",
                  "streams": [run(width) for width in (16, 32, 64)]},
                 separators=(",", ":")))
