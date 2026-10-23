"""Independent rich-to-simple replay for H066 at fresh seeds."""

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from candidates.return_budget_growth.principle import System


def run(width):
    rng = random.Random(61007 + width)
    pairs = [(i, i + 1) for i in range(0, width - 1, 2)]
    previous = [rng.randrange(2) for _ in range(width)]
    system = System()
    phases = []
    for name, active in (("rich", pairs), ("simple", [])):
        losses = []
        counts = []
        for tick in range(640):
            current = [rng.randrange(2) for _ in range(width)]
            for source, target in active:
                current[target] = previous[source]
            prediction = system.step(current)
            losses.extend((current[i] - prediction[i]) ** 2 for i in range(width))
            previous[:] = current
            if tick >= 128 and tick % 16 == 0:
                counts.append(system.structure()["connections"])
        phases.append({
            "phase": name,
            "brier": sum(losses) / len(losses),
            "mean_connections": sum(counts) / len(counts),
            **system.structure(),
        })
    return {"width": width, "phases": phases}


if __name__ == "__main__":
    result = {"candidate": "return_budget_growth", "seed_base": 61007,
              "runs": [run(width) for width in (8, 16, 32, 64)]}
    output = Path(__file__).with_name("eksperymentator_h066_replay.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print([(row["width"], [(phase["phase"], round(phase["brier"], 4),
                            round(phase["mean_connections"], 1),
                            phase["connections"], phase["memory_bytes"])
                            for phase in row["phases"]]) for row in result["runs"]])
