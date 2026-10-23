"""Independent paired rerun of the H005 typed-resource-flow experiment."""

import importlib.util
import json
from pathlib import Path
import sys


SOURCE = Path(__file__).parents[1] / "theory/theorist_life/sim/resource_flux_tagged_fission.py"
SPEC = importlib.util.spec_from_file_location("h005_source", SOURCE)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def mean(values):
    values = list(values)
    return sum(values) / len(values)


def measure(rows):
    grouped = {}
    for row in rows:
        grouped.setdefault(row["condition"], []).append(row)
    result = {}
    for condition, values in grouped.items():
        samples = [item for row in values for item in MODULE.measurement(row)]
        result[condition] = {
            "active_edge_share": mean(item["matching_source_fraction"] for item in samples),
            "target_mse": mean(item["population_target_mse"] for item in samples),
            "runs": len(values),
        }
    return result


def paired(rows, left, right):
    grouped = {(row["seed"], row["condition"]): row for row in rows}
    seeds = sorted({row["seed"] for row in rows})
    share = []
    mse = []
    for seed in seeds:
        a = MODULE.measurement(grouped[(seed, left)])
        b = MODULE.measurement(grouped[(seed, right)])
        share.append(mean(x["matching_source_fraction"] for x in a)
                     - mean(x["matching_source_fraction"] for x in b))
        mse.append(mean(x["population_target_mse"] for x in a)
                   - mean(x["population_target_mse"] for x in b))
    return {
        "active_share_left_minus_right": mean(share),
        "target_mse_left_minus_right": mean(mse),
        "active_share_same_direction": sum(value > 0 for value in share),
        "target_mse_same_direction": sum(value < 0 for value in mse),
    }


def main():
    kwargs = {"steps": 3200, "segment_length": 800, "schedule": [0, 1, 2, 0],
              "source_count": 3, "initial_population": 45, "initial_sources": [0, 1],
              "initial_mass": 1.0, "substrate_inflow": 7.7625,
              "maintenance": 0.10, "error_cost": 0.25, "flip_probability": 0.08}
    conditions = ("selected_tagged_fission", "neutral_tagged_fission",
                  "selected_untyped_fission")
    rows = [MODULE.run(seed, condition, **kwargs)
            for seed in range(30) for condition in conditions]
    compact = [{key: value for key, value in row.items() if key != "trace"} for row in rows]
    result = {"parameters": kwargs, "summary": measure(rows), "runs": compact,
              "paired_selected_minus_neutral": paired(rows, conditions[0], conditions[1]),
              "paired_selected_minus_untyped": paired(rows, conditions[0], conditions[2])}
    output = Path(__file__).with_name("h005-independent") / "result.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"output": str(output), "summary": result["summary"],
                      "paired_selected_minus_neutral": result["paired_selected_minus_neutral"],
                      "paired_selected_minus_untyped": result["paired_selected_minus_untyped"]},
                     indent=2))


if __name__ == "__main__":
    main()
