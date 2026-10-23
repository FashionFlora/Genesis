"""Pair audit of the two current coactivity leaders; never calls sandbox/judge."""

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
    "flux_scale9": ROOT / "candidates/coactivity_flux_scale9/principle.py",
    "support_resilient": ROOT / "candidates/coactivity_support_resilient/principle.py",
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


def observations(width, steps, seed):
    rng = random.Random(seed)
    return [[rng.getrandbits(1) for _ in range(width)] for _ in range(steps)]


def winner_map(system):
    winners = []
    for target in range(system.width):
        def gap(source):
            cell = system.counts[source][target]
            return abs((cell[1][1] + 1.0) / (cell[1][0] + 2.0)
                       - (cell[0][1] + 1.0) / (cell[0][0] + 2.0))
        winners.append(max(range(system.width), key=gap))
    return winners


def normalized_ast(path):
    tree = ast.parse(path.read_text())
    tree.body[0] = ast.Pass()  # remove candidate-specific docstring
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "PARAMS"
                for target in node.targets):
            node.value = ast.Constant("TIMESCALE")
    return ast.dump(tree, include_attributes=False)


def matched_rule_check(timescale=9, width=16, steps=300):
    modules = {name: load(path, "matched_" + name)
               for name, path in PATHS.items()}
    modules["support_resilient"].PARAMS["timescale"] = timescale
    modules["flux_scale9"].PARAMS["timescale"] = timescale
    obs = observations(width, steps, 4417)
    systems = {name: module.System() for name, module in modules.items()}
    predictions = {
        name: [system.step(item) for item in obs]
        for name, system in systems.items()
    }
    mismatches = sum(
        any(abs(a - b) > 1.0e-12
            for a, b in zip(predictions["flux_scale9"][i],
                            predictions["support_resilient"][i]))
        for i in range(steps)
    )
    return {
        "timescale": timescale,
        "prediction_mismatch_steps": mismatches,
        "winner_maps_equal": winner_map(systems["flux_scale9"]) ==
        winner_map(systems["support_resilient"]),
    }


def predictive_sanity(name):
    module = load(PATHS[name], "predictive_" + name)
    module.PARAMS["timescale"] = 9 if name == "flux_scale9" else 16
    system = module.System()
    rng = random.Random(991)
    stream = [[rng.getrandbits(1) for _ in range(8)]]
    for _ in range(2000):
        previous = stream[-1]
        nxt = [rng.getrandbits(1) for _ in range(8)]
        nxt[7] = previous[0] if rng.random() < 0.9 else 1 - previous[0]
        stream.append(nxt)
    predictive = []
    for i in range(2000):
        prediction = system.step(stream[i])
        predictive.append((prediction[7] - stream[i + 1][7]) ** 2)
    module = load(PATHS[name], "iid_" + name)
    module.PARAMS["timescale"] = 9 if name == "flux_scale9" else 16
    system = module.System()
    rng = random.Random(1991)
    iid = [[rng.getrandbits(1) for _ in range(8)] for _ in range(2001)]
    null = []
    for i in range(2000):
        prediction = system.step(iid[i])
        null.append((prediction[7] - iid[i + 1][7]) ** 2)
    return {
        "predictive_brier": sum(predictive) / len(predictive),
        "iid_brier": sum(null) / len(null),
        "predictive_tail_brier": sum(predictive[-400:]) / 400,
        "iid_tail_brier": sum(null[-400:]) / 400,
    }


def scaling():
    rows = []
    for width in (8, 16, 32, 64):
        obs = observations(width, 160, 8100 + width)
        row = {"width": width, "dense_cells": width * width, "candidates": {}}
        for name, path in PATHS.items():
            module = load(path, "scale_" + name + str(width))
            start = time.perf_counter()
            system = module.System()
            for item in obs:
                system.step(item)
            row["candidates"][name] = {
                "elapsed_seconds": time.perf_counter() - start,
                "deep_python_state_bytes": deep_size(vars(system)),
                "reported_structure": system.structure(),
            }
        rows.append(row)
    return rows


def structure_collision():
    rows = []
    for seed in (1, 2):
        module = load(PATHS["support_resilient"], "collision_" + str(seed))
        system = module.System()
        rng = random.Random(seed)
        for _ in range(240):
            system.step([rng.getrandbits(1) for _ in range(16)])
        rows.append({"seed": seed, "connections": system.structure()["connections"],
                     "winner_map": winner_map(system)})
    return {
        "same_connection_count": rows[0]["connections"] == rows[1]["connections"],
        "different_winner_maps": rows[0]["winner_map"] != rows[1]["winner_map"],
        "runs": rows,
    }


def leaderboard_summary():
    rows = []
    for line in (ROOT / "sandbox/leaderboard.jsonl").read_text().splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("candidate") in {"coactivity_flux_scale9", "coactivity_support_resilient"}:
            rows.append({k: row.get(k) for k in (
                "evaluated_at_utc", "candidate", "author", "score",
                "score_unpenalized", "params", "highest_passed_level", "stop_reason")})
    return rows


def main():
    source = {}
    for name, path in PATHS.items():
        source[name] = {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "normalized_ast_sha256": hashlib.sha256(
                normalized_ast(path).encode()).hexdigest(),
            "imports": [type(node).__name__ for node in ast.walk(ast.parse(path.read_text()))
                        if isinstance(node, (ast.Import, ast.ImportFrom))],
            "nominal_timescale": load(path, "source_" + name).PARAMS["timescale"],
        }
    payload = {
        "protocol": "fresh deterministic pair audit; no sandbox judge",
        "source": source,
        "normalized_ast_equal": source["flux_scale9"]["normalized_ast_sha256"] ==
        source["support_resilient"]["normalized_ast_sha256"],
        "matched_rule": matched_rule_check(),
        "prediction_sanity": {name: predictive_sanity(name) for name in PATHS},
        "scaling": scaling(),
        "structure_collision": structure_collision(),
        "leaderboard_rows": leaderboard_summary(),
        "prior_art_opened": {
            "source": "Frégnac et al., 2010, PMC3059677",
            "finding": "rate-based covariance/generalized Hebbian rules use pre/post activity correlation; the family predates both candidates",
        },
    }
    out = ROOT / "audit/tournament_flux_resilient_result_20261022.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(out)
    print(json.dumps(payload, separators=(",", ":")))


if __name__ == "__main__":
    main()
