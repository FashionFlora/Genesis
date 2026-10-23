"""Fresh audit of the two coactivity candidates; this does not call the judge."""

import ast
import hashlib
import importlib.util
import json
import random
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATHS = {
    "resilient": ROOT / "candidates/coactivity_support_resilient/principle.py",
    "clean": ROOT / "candidates/coactivity_support_clean/principle.py",
}


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


def winner_map(agent):
    winners = []
    for target in range(agent.width):
        def gap(source):
            cell = agent.counts[source][target]
            return abs((cell[1][1] + 1.0) / (cell[1][0] + 2.0)
                       - (cell[0][1] + 1.0) / (cell[0][0] + 2.0))
        winners.append(max(range(agent.width), key=gap))
    return winners


def observations(width, steps, seed):
    rng = random.Random(seed)
    return [[rng.getrandbits(1) for _ in range(width)] for _ in range(steps)]


def run(module_name, width, obs):
    module = load(PATHS[module_name], "pair_%s_%d" % (module_name, width))
    start = time.perf_counter()
    system = module.System()
    predictions = [system.step(item) for item in obs]
    elapsed = time.perf_counter() - start
    return system, predictions, elapsed


def target_prediction_sanity():
    """Check that lower error reflects a next-observation relation, not a constant."""
    result = {}
    for name in PATHS:
        module = load(PATHS[name], "sanity_%s" % name)
        system = module.System()
        rng = random.Random(991)
        observations = [[rng.getrandbits(1) for _ in range(8)]]
        for _ in range(4000):
            previous = observations[-1]
            next_observation = [rng.getrandbits(1) for _ in range(8)]
            next_observation[7] = (previous[0] if rng.random() < 0.9
                                   else 1 - previous[0])
            observations.append(next_observation)
        predictive = []
        for index in range(4000):
            prediction = system.step(observations[index])
            predictive.append((prediction[7] - observations[index + 1][7]) ** 2)

        module = load(PATHS[name], "sanity_iid_%s" % name)
        system = module.System()
        rng = random.Random(1991)
        iid = [[rng.getrandbits(1) for _ in range(8)] for _ in range(4001)]
        null = []
        for index in range(4000):
            prediction = system.step(iid[index])
            null.append((prediction[7] - iid[index + 1][7]) ** 2)
        result[name] = {
            "predictive_target_brier": sum(predictive) / len(predictive),
            "iid_target_brier": sum(null) / len(null),
            "predictive_tail_brier": sum(predictive[-800:]) / 800,
            "iid_tail_brier": sum(null[-800:]) / 800,
        }
    return result


def configure(decay_mode):
    modules = {name: load(path, "configure_%s_%s" % (name, decay_mode))
               for name, path in PATHS.items()}
    resilient_decay = modules["resilient"].PARAMS["timescale"] / (
        modules["resilient"].PARAMS["timescale"] + 1.0)
    clean_decay = min(modules["clean"].PARAMS["decay"], 1.0)
    if decay_mode == "resilient":
        modules["clean"].PARAMS["decay"] = resilient_decay
    elif decay_mode == "clean":
        modules["resilient"].PARAMS["timescale"] = clean_decay / (1.0 - clean_decay)
    return modules, resilient_decay, clean_decay


def matched_check(mode, width=16, steps=200):
    modules, resilient_decay, clean_decay = configure(mode)
    obs = observations(width, steps, 4417)
    systems = {}
    predictions = {}
    for name, module in modules.items():
        system = module.System()
        systems[name] = system
        predictions[name] = [system.step(item) for item in obs]
    mismatches = sum(
        any(abs(a - b) > 1.0e-12 for a, b in zip(predictions["resilient"][i], predictions["clean"][i]))
        for i in range(steps)
    )
    return {
        "mode": mode,
        "resilient_decay": resilient_decay if mode == "resilient" else clean_decay,
        "clean_decay": resilient_decay if mode == "resilient" else clean_decay,
        "prediction_mismatch_steps": mismatches,
        "winner_maps_equal": winner_map(systems["resilient"]) == winner_map(systems["clean"]),
    }


def source_facts():
    result = {}
    for name, path in PATHS.items():
        source = path.read_bytes()
        tree = ast.parse(source)
        result[name] = {
            "sha256": hashlib.sha256(source).hexdigest(),
            "imports": [node.__class__.__name__ for node in ast.walk(tree)
                        if isinstance(node, (ast.Import, ast.ImportFrom))],
            "has_file_io": any(isinstance(node, ast.Call)
                               and isinstance(node.func, ast.Name)
                               and node.func.id in {"open", "exec", "eval"}
                               for node in ast.walk(tree)),
        }
    rows = []
    for line in (ROOT / "sandbox/leaderboard.jsonl").read_text().splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("candidate") in {"coactivity_support_resilient", "coactivity_support_clean"}:
            rows.append({"candidate": row["candidate"],
                         "evaluated_at_utc": row.get("evaluated_at_utc"),
                         "score": row.get("score"),
                         "params": row.get("params"),
                         "principle_sha256": row.get("principle_sha256")})
    result["leaderboard_tail"] = rows[-30:]
    return result


def structure_and_scaling():
    rows = []
    for width in (8, 16, 32, 64):
        obs = observations(width, 160, 8100 + width)
        entry = {"width": width, "steps": len(obs), "candidates": {}}
        for name in PATHS:
            system, _, elapsed = run(name, width, obs)
            winners = winner_map(system)
            cross_half = sum(target >= width // 2 and source < width // 2
                             for target, source in enumerate(winners))
            entry["candidates"][name] = {
                "elapsed_seconds": elapsed,
                "deep_python_state_bytes": deep_size(vars(system)),
                "dense_cells": width * width,
                "reported_structure": system.structure(),
                "winner_map": winners,
                "winner_map_cross_half": cross_half,
            }
        rows.append(entry)
    return rows


def structure_collision():
    """Show that the scalar connection count aliases different winner maps."""
    maps = []
    for seed in (1, 2):
        module = load(PATHS["resilient"], "collision_%d" % seed)
        system = module.System()
        rng = random.Random(seed)
        for _ in range(240):
            system.step([rng.getrandbits(1) for _ in range(16)])
        maps.append({"seed": seed,
                     "connections": system.structure()["connections"],
                     "winner_map": winner_map(system)})
    return {
        "same_reported_connections": maps[0]["connections"] == maps[1]["connections"],
        "different_winner_maps": maps[0]["winner_map"] != maps[1]["winner_map"],
        "runs": maps,
    }


def main():
    payload = {
        "protocol": "fresh deterministic audit; no sandbox judge; shared Bernoulli streams",
        "source": source_facts(),
        "current_decay": {
            "resilient": 16.0 / 17.0,
            "clean": 0.97,
            "absolute_difference": abs(16.0 / 17.0 - 0.97),
        },
        "matched_decay": [matched_check("resilient"), matched_check("clean")],
        "prediction_sanity": target_prediction_sanity(),
        "scaling_and_structure": structure_and_scaling(),
        "structure_collision": structure_collision(),
    }
    out = ROOT / "audit/tournament_pair_20261022_result.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(out)
    print(json.dumps(payload, separators=(",", ":")))


if __name__ == "__main__":
    main()
