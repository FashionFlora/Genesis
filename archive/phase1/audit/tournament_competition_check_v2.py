"""Independent audit of structural claims in the two tournament candidates."""

import importlib.util
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    path = ROOT / "candidates" / name / "principle.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.System()


def coactivity_winners(system, observation):
    winners = []
    for target in range(system.width):
        def gap(source):
            cell = system.counts[source][target]
            return abs((cell[1][1] + 1.0) / (cell[1][0] + 2.0)
                       - (cell[0][1] + 1.0) / (cell[0][0] + 2.0))
        source = max(range(system.width), key=gap)
        winners.append([source, target])
    return winners


def audit_coactivity(width=8, steps=80):
    rows = []
    for label, generator in (
        ("all_zero", lambda rng: [0] * width),
        ("random", lambda rng: [rng.randrange(2) for _ in range(width)]),
    ):
        system = load("coactivity_support")
        rng = random.Random(7400 + len(label))
        obs = generator(rng)
        for _ in range(steps):
            nxt = generator(rng)
            system.step(obs)
            obs = nxt
        winners = coactivity_winners(system, obs)
        report_count = system.edges
        actual_cross_partition = sum(
            target >= width // 2 and source < width // 2
            for source, target in winners
        )
        rows.append({
            "stream": label,
            "reported_connections": report_count,
            "winner_pairs": winners,
            "actual_cross_partition_connections": actual_cross_partition,
            "reported_matches_actual_partition_count": report_count == actual_cross_partition,
        })
    collision = None
    seen = {}
    for seed in range(100):
        system = load("coactivity_support")
        rng = random.Random(7500 + seed)
        obs = [rng.randrange(2) for _ in range(width)]
        for _ in range(steps):
            nxt = [rng.randrange(2) for _ in range(width)]
            system.step(obs)
            obs = nxt
        winners = tuple(tuple(pair) for pair in coactivity_winners(system, obs))
        key = system.edges
        if key in seen and seen[key]["winner_pairs"] != winners:
            collision = {
                "reported_connections": key,
                "first_winner_pairs": seen[key]["winner_pairs"],
                "second_winner_pairs": winners,
                "seeds": [seen[key]["seed"], seed],
            }
            break
        seen[key] = {"seed": seed, "winner_pairs": winners}
    return {"streams": rows, "same_count_different_winners": collision}


def audit_resource_flow(width=8, steps=200):
    system = load("resource_flow_competition")
    rng = random.Random(7411)
    obs = [rng.randrange(2) for _ in range(width)]
    for _ in range(steps):
        nxt = [rng.randrange(2) for _ in range(width)]
        system.step(obs)
        obs = nxt
    pairs = [(cell[0], cell[1]) for cell in system.cells]
    distinct = sorted(set(pairs))
    expected = width * width
    return {
        "width": width,
        "steps": steps,
        "initial_repertoire_size": expected,
        "final_cell_copies": len(pairs),
        "final_distinct_edge_types": len(distinct),
        "all_initial_types_still_present": len(distinct) == expected,
        "duplicate_copies": len(pairs) - len(distinct),
    }


if __name__ == "__main__":
    result = {
        "coactivity": audit_coactivity(),
        "resource_flow": audit_resource_flow(),
    }
    output = ROOT / "audit/tournament_competition_check_v2_result.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(output)
    print(json.dumps(result, sort_keys=True))
