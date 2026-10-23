"""Measure adaptive_contact_flux structure across relation-rich and simple phases."""

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from candidates.adaptive_contact_flux.principle import System


def run(width, seed=731):
    rng = random.Random(seed + width)
    system = System()
    pairs = [(i, i + 1) for i in range(0, width - 1, 2)]
    phases = []
    previous = [rng.randrange(2) for _ in range(width)]

    def phase(name, active):
        errors = []
        counts = []
        for tick in range(640):
            current = [rng.randrange(2) for _ in range(width)]
            for source, target in active:
                current[target] = previous[source]
            prediction = system.step(current)
            errors.extend((current[i] - prediction[i]) ** 2 for i in range(width))
            previous[:] = current
            if tick >= 128 and tick % 16 == 0:
                counts.append(system.structure()["connections"])
        phases.append({
            "phase": name,
            "mean_brier": sum(errors) / len(errors),
            "mean_connections": sum(counts) / max(1, len(counts)),
            "end_connections": system.structure()["connections"],
            "memory_bytes": system.structure()["memory_bytes"],
        })

    phase("rich", pairs)
    phase("simple", [])
    return {"width": width, "active_relations": len(pairs), "phases": phases}


if __name__ == "__main__":
    result = {"candidate": "adaptive_contact_flux", "runs": [run(w) for w in (8, 16, 32, 64)]}
    path = Path(__file__).with_name("phase_probe_result.json")
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for row in result["runs"]:
        print(row["width"], row["active_relations"],
              [(p["phase"], round(p["mean_brier"], 4),
                round(p["mean_connections"], 2), p["end_connections"], p["memory_bytes"])
               for p in row["phases"]])
    print(path)
