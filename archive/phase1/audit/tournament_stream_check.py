"""Independent comparison of the two clean stream candidates.

This audit uses only the public System.step(obs) interface and writes no
candidate or sandbox artifacts.  It measures return-to-A error, a nonlinear
two-source XOR control, and wall time at increasing widths.
"""

from __future__ import annotations

import importlib.util
import json
import random
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = {
    "coactivity_support": ROOT / "candidates/coactivity_support/principle.py",
    "predictive_homeostasis_clean": ROOT / "candidates/predictive_homeostasis_clean/principle.py",
}


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem + str(path), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.System()


def observation_stream(seed, width=8, segment=400):
    """Yield current obs, next obs, and phase for A-B-A-C-B-A."""
    rng = random.Random(seed)
    obs = [float(rng.randrange(2)) for _ in range(width)]
    schedule = (0, 1, 0, 2, 1, 0)
    sources = (0, 1, 2)
    target = width - 1
    for step in range(segment * len(schedule)):
        phase = step // segment
        source = sources[schedule[phase]]
        nxt = [float(rng.randrange(2)) for _ in range(width)]
        nxt[target] = obs[source] if rng.random() >= 0.10 else 1.0 - obs[source]
        yield obs, nxt, phase
        obs = nxt


def return_test(path, seeds=(1103, 2029, 7919), width=8, segment=400):
    rows = []
    for seed in seeds:
        system = load(path)
        errors = [[] for _ in range(6)]
        started = time.perf_counter()
        for obs, nxt, phase in observation_stream(seed, width, segment):
            prediction = system.step(obs)
            errors[phase].append((float(prediction[-1]) - nxt[-1]) ** 2)
        elapsed = time.perf_counter() - started
        # The two later A visits test memory after intervening B/C evidence.
        return_gaps = []
        for phase in (2, 5):
            return_gaps.append(
                sum(errors[phase][:50]) / 50.0 - sum(errors[0 if phase == 2 else 2][-50:]) / 50.0
            )
        rows.append({
            "seed": seed,
            "return_forgetting_mse": sum(return_gaps) / len(return_gaps),
            "a_return_gaps": return_gaps,
            "wall_seconds": elapsed,
        })
    return rows


def xor_test(path, seed=1103, width=8, steps=4000):
    rng = random.Random(seed)
    system = load(path)
    obs = [float(rng.randrange(2)) for _ in range(width)]
    errors = []
    for _ in range(steps):
        nxt = [float(rng.randrange(2)) for _ in range(width)]
        nxt[-1] = float(int(obs[0]) ^ int(obs[1])) if rng.random() >= 0.10 else float(1 - (int(obs[0]) ^ int(obs[1])))
        prediction = system.step(obs)
        errors.append((float(prediction[-1]) - nxt[-1]) ** 2)
        obs = nxt
    return {
        "first_half_mse": sum(errors[: steps // 2]) / (steps // 2),
        "last_half_mse": sum(errors[steps // 2 :]) / (steps // 2),
    }


def scaling(path, widths=(8, 16, 32, 64), steps=100):
    rows = []
    for width in widths:
        system = load(path)
        rng = random.Random(1000 + width)
        obs = [float(rng.randrange(2)) for _ in range(width)]
        started = time.perf_counter()
        for _ in range(steps):
            nxt = [float(rng.randrange(2)) for _ in range(width)]
            system.step(obs)
            obs = nxt
        structure = system.structure()
        rows.append({"width": width, "seconds": time.perf_counter() - started, "structure": structure})
    return rows


if __name__ == "__main__":
    output = {}
    for name, path in CANDIDATES.items():
        output[name] = {
            "return_test": return_test(path),
            "xor_test": xor_test(path),
            "scaling": scaling(path),
        }
    print(json.dumps(output, sort_keys=True))
