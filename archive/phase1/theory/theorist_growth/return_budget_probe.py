"""Rich-to-simple structural and prediction probe across channel widths."""

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from candidates.return_budget_growth.principle import System


def run(width):
    rng = random.Random(9901 + width)
    pairs = [(i, i + 1) for i in range(0, width - 1, 2)]
    previous = [rng.randrange(2) for _ in range(width)]
    system = System()
    out = []
    for name, active in (("rich", pairs), ("simple", [])):
        loss, counts = [], []
        for tick in range(640):
            current = [rng.randrange(2) for _ in range(width)]
            for source, target in active:
                current[target] = previous[source]
            prediction = system.step(current)
            loss.extend((current[i] - prediction[i]) ** 2 for i in range(width))
            previous[:] = current
            if tick >= 128 and tick % 16 == 0:
                counts.append(system.structure()["connections"])
        state = system.structure()
        out.append({"phase": name, "brier": sum(loss) / len(loss),
                    "mean_connections": sum(counts) / len(counts), **state})
    return {"width": width, "pairs": len(pairs), "phases": out}


if __name__ == "__main__":
    result = {"candidate": "return_budget_growth",
              "runs": [run(n) for n in (8, 16, 32, 64)]}
    path = Path(__file__).with_name("return_budget_result.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    for row in result["runs"]:
        print(row["width"], [(p["phase"], round(p["brier"], 4),
                              round(p["mean_connections"], 1), p["connections"],
                              p["memory_bytes"]) for p in row["phases"]])
