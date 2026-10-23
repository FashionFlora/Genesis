"""Small public-interface audit for the coactivity/resource-flow tournament."""

import importlib.util
import json
import random
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = {
    "coactivity_support": ROOT / "candidates/coactivity_support/principle.py",
    "resource_flow_competition": ROOT / "candidates/resource_flow_competition/principle.py",
}


def load(path):
    spec = importlib.util.spec_from_file_location(path.parent.name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.System()


def measure(name, path, widths=(8, 16, 32), steps=80):
    rows = []
    for width in widths:
        system = load(path)
        rng = random.Random(4100 + width)
        obs = [rng.randrange(2) for _ in range(width)]
        start = time.perf_counter()
        for _ in range(steps):
            nxt = [rng.randrange(2) for _ in range(width)]
            system.step(obs)
            obs = nxt
        elapsed = time.perf_counter() - start
        state = system.structure()
        row = {"width": width, "steps": steps, "seconds": elapsed,
               "structure": state}
        if name == "resource_flow_competition":
            edges = [(cell[0], cell[1]) for cell in system.cells]
            row["distinct_edge_types"] = len(set(edges))
            row["cell_copies"] = len(edges)
            row["duplicate_cells"] = len(edges) - len(set(edges))
        else:
            row["allocated_edge_slots"] = sum(len(target) for source in system.counts for target in source)
            row["reported_edges"] = system.edges
        rows.append(row)
    return rows


if __name__ == "__main__":
    result = {name: measure(name, path) for name, path in CANDIDATES.items()}
    output = ROOT / "audit/tournament_competition_check_result.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(output)
    print(json.dumps(result, sort_keys=True))
