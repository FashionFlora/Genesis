"""Compare the two coactivity candidates on identical deterministic inputs."""

import importlib.util
import json
import random
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAIRS = {
    "coactivity_support": ROOT / "candidates/coactivity_support/principle.py",
    "coactivity_support_clean": ROOT / "candidates/coactivity_support_clean/principle.py",
}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def deep_size(value, seen=None):
    if seen is None:
        seen = set()
    identity = id(value)
    if identity in seen:
        return 0
    seen.add(identity)
    size = sys.getsizeof(value)
    if isinstance(value, dict):
        size += sum(deep_size(k, seen) + deep_size(v, seen) for k, v in value.items())
    elif isinstance(value, (list, tuple, set)):
        size += sum(deep_size(item, seen) for item in value)
    elif hasattr(value, "__dict__"):
        size += deep_size(vars(value), seen)
    return size


def run_width(width, steps=120):
    modules = {name: load(path, f"audit_{name}_{width}") for name, path in PAIRS.items()}
    agents = {name: module.System() for name, module in modules.items()}
    rng = random.Random(8137 + width)
    observations = [[rng.getrandbits(1) for _ in range(width)] for _ in range(steps)]
    mismatches = 0
    elapsed = {}
    for name, agent in agents.items():
        start = time.perf_counter()
        for step, observation in enumerate(observations):
            prediction = agent.step(observation)
            if name == "coactivity_support":
                run_width.predictions[width].append(prediction)
            elif prediction != run_width.predictions[width][step]:
                mismatches += 1
        elapsed[name] = time.perf_counter() - start
    report = {}
    for name, agent in agents.items():
        state = vars(agent)
        report[name] = {
            "elapsed_seconds": elapsed[name],
            "reported_memory_bytes": agent.structure()["memory_bytes"],
            "deep_python_state_bytes": deep_size(state),
            "final_structure": agent.structure(),
        }
    return {"width": width, "steps": steps, "prediction_mismatch_steps": mismatches,
            "candidates": report}


run_width.predictions = {}


def main():
    results = []
    for width in (8, 16, 32, 64):
        run_width.predictions[width] = []
        results.append(run_width(width))
    payload = {
        "protocol": "120 deterministic Bernoulli observations per width; both candidates receive identical inputs",
        "widths": results,
        "interpretation": "Nominal prediction equality checks implementation equivalence; timings and deep state sizes are local diagnostics, not judge scores.",
    }
    out = ROOT / "audit/coactivity_pair_audit_result.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(out)
    print(json.dumps(results, separators=(",", ":")))


if __name__ == "__main__":
    main()
