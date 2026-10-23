"""Audit newly reported coactivity leaderboard candidates without judging them."""

import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def deep_size(value, seen=None):
    if seen is None:
        seen = set()
    if id(value) in seen:
        return 0
    seen.add(id(value))
    size = sys.getsizeof(value)
    if isinstance(value, dict):
        size += sum(deep_size(k, seen) + deep_size(v, seen)
                    for k, v in value.items())
    elif isinstance(value, (list, tuple, set)):
        size += sum(deep_size(item, seen) for item in value)
    elif hasattr(value, "__dict__"):
        size += deep_size(vars(value), seen)
    return size


def predictions(module, observations):
    system = module.System()
    return [system.step(item) for item in observations], system


def clone_check(timescale):
    resilient = load(ROOT / "candidates/coactivity_support_resilient/principle.py",
                     "resilient_%d" % timescale)
    clone = load(ROOT / ("candidates/coactivity_flux_scale%d/principle.py" % timescale),
                 "clone_%d" % timescale)
    resilient.PARAMS["timescale"] = timescale
    rng = random.Random(9127 + timescale)
    observations = [[rng.getrandbits(1) for _ in range(16)] for _ in range(240)]
    left, left_system = predictions(resilient, observations)
    right, right_system = predictions(clone, observations)
    mismatch = sum(
        any(abs(a - b) > 1e-12 for a, b in zip(left[i], right[i]))
        for i in range(len(observations))
    )
    return {"timescale": timescale, "prediction_mismatch_steps": mismatch,
            "reported_structure_equal": left_system.structure() == right_system.structure(),
            "same_source_hash": hashlib.sha256(
                (ROOT / "candidates/coactivity_support_resilient/principle.py").read_bytes()
            ).hexdigest() == hashlib.sha256(
                (ROOT / ("candidates/coactivity_flux_scale%d/principle.py" % timescale)).read_bytes()
            ).hexdigest()}


def state_sizes():
    rows = []
    for name in ("coactivity_support_resilient", "coactivity_context_blend",
                 "coactivity_flux_adaptive", "coactivity_single_support"):
        path = ROOT / "candidates" / name / "principle.py"
        module = load(path, "size_" + name)
        system = module.System()
        for _ in range(120):
            system.step([random.Random(77).getrandbits(1) for _ in range(16)])
        rows.append({"candidate": name, "deep_python_state_bytes": deep_size(vars(system)),
                     "reported_structure": system.structure()})
    return rows


def leaderboard_rows():
    wanted = {"coactivity_context_blend", "coactivity_flux_scale9",
              "coactivity_flux_scale11", "coactivity_flux_adaptive",
              "coactivity_single_support"}
    rows = []
    for line in (ROOT / "sandbox/leaderboard.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("candidate") in wanted:
            rows.append({"candidate": row["candidate"], "evaluated_at_utc": row.get("evaluated_at_utc"),
                         "score": row.get("score"), "params": row.get("params"),
                         "author": row.get("author"), "only_level": row.get("protocol", {}).get("only_level"),
                         "highest_passed_level": row.get("highest_passed_level"),
                         "stop_reason": row.get("stop_reason")})
    return rows


def main():
    payload = {
        "protocol": "static and deterministic clone audit; no sandbox judge",
        "clone_checks": [clone_check(9), clone_check(11)],
        "state_sizes": state_sizes(),
        "leaderboard_rows": leaderboard_rows(),
        "interpretation": {
            "scale9_scale11": "exact same update as resilient after matching timescale; parameter variants are not new mechanisms",
            "context_blend": "adds context-indexed counters and evidence blend, increasing state by a contexts factor",
            "adaptive": "adds per-cell contrast-dependent decay, a separate mechanism and calibration-only result",
            "single_support": "uses one covariance float per pair but remains dense and has no full level-2 result",
        },
    }
    out = ROOT / "audit/new_entries_20261022_result.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(out)
    print(json.dumps(payload, separators=(",", ":")))


if __name__ == "__main__":
    main()
