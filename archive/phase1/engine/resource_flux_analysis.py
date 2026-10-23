"""Paired analysis for H003 resource-flux stream_bench runs."""

import argparse
import json
import statistics
from pathlib import Path


AGENT_GROUPS = {
    "ResourceSelected": ("selected", 1.0),
    "ResourceNeutral": ("neutral_mu_0.05", 1.0),
    "ResourceNeutralHighMutation": ("neutral_mu_0.15", 1.0),
    "ResourceSelectedLowSupply": ("selected", 0.9),
    "ResourceNeutralLowSupply": ("neutral_mu_0.05", 0.9),
    "ResourceNeutralHighMutationLowSupply": ("neutral_mu_0.15", 0.9),
    "ResourceSelectedHighSupply": ("selected", 1.1),
    "ResourceNeutralHighSupply": ("neutral_mu_0.05", 1.1),
    "ResourceNeutralHighMutationHighSupply": ("neutral_mu_0.15", 1.1),
}


def _mean_sd(values):
    values = [float(value) for value in values if value is not None]
    return {
        "mean": statistics.mean(values) if values else None,
        "sd": statistics.stdev(values) if len(values) > 1 else (0.0 if values else None),
    }


def _paired(selected, control, field):
    left = {row["seed"]: row[field] for row in selected}
    right = {row["seed"]: row[field] for row in control}
    seeds = sorted(seed for seed in set(left) & set(right)
                   if left[seed] is not None and right[seed] is not None)
    differences = [left[seed] - right[seed] for seed in seeds]
    mean = statistics.mean(differences) if differences else None
    sd = statistics.stdev(differences) if len(differences) > 1 else 0.0
    t_critical = {10: 2.262, 20: 2.093}.get(len(differences), 1.96)
    half_width = t_critical * sd / (len(differences) ** 0.5) if differences else None
    return {
        "n_paired": len(differences),
        "mean_selected_minus_control": mean,
        "sd_paired_difference": sd,
        "95pct_t_interval": [mean - half_width, mean + half_width]
        if mean is not None else None,
        "fraction_selected_better": (
            sum(value > 0.0 if field in {
                "mean_post_shift_active_source_edge_share_100_300",
                "mean_post_shift_active_source_resource_mass_share_100_300",
            }
                else value < 0.0 for value in differences) / len(differences)
            if differences else None
        ),
        "differences": differences,
    }


def analyze(input_path, output_dir=None):
    raw = json.loads(Path(input_path).read_text(encoding="utf-8"))
    groups = {}
    rows = []
    for run in raw["runs"]:
        class_name = run["agent"].rsplit(":", 1)[-1]
        if class_name not in AGENT_GROUPS:
            continue
        condition, inflow_scale = AGENT_GROUPS[class_name]
        structure = run["structure_final"]
        item = {
            "seed": run["seed"],
            "agent": class_name,
            "condition": condition,
            "inflow_scale": inflow_scale,
            "mean_online_mse": run["mean_online_mse"],
            "mean_target_mse": run["mean_target_mse"],
            "mean_adaptation_steps_after_change": run["mean_adaptation_steps_after_change"],
            "mean_return_forgetting_mse": run["mean_return_forgetting_mse"],
            "mean_post_shift_active_source_edge_share_100_300":
                run["mean_post_shift_active_source_edge_share_100_300"],
            "mean_post_shift_active_source_resource_mass_share_100_300":
                run["mean_post_shift_active_source_resource_mass_share_100_300"],
            "final_population": structure["population"],
            "final_distinct_source_edges": structure["distinct_connections"],
            "births": structure["births"],
            "deaths": structure["deaths"],
            "mutations": structure["mutations"],
            "resource_packets": structure["resource_packets"],
            "error_resource_cost": structure["error_resource_cost"],
            "mean_cellwise_prediction_mse": structure["mean_cellwise_prediction_mse"],
            "extinct_at_step": structure["extinct_at_step"],
            "work_units": structure["work_units"],
            "agent_cpu_seconds": run["cost"]["agent_seconds"],
            "run_wall_seconds": run["cost"]["wall_seconds"],
            "estimated_state_bytes": structure["estimated_state_bytes"],
            "peak_structure": max(
                point["population"] for point in run["structure_timeline"]
            ),
        }
        rows.append(item)
        groups.setdefault((condition, inflow_scale), []).append(item)

    summaries = {}
    fields = (
        "mean_post_shift_active_source_edge_share_100_300", "mean_target_mse",
        "mean_post_shift_active_source_resource_mass_share_100_300",
        "mean_online_mse", "mean_adaptation_steps_after_change",
        "mean_return_forgetting_mse", "final_population", "peak_structure",
        "births", "deaths", "mutations", "resource_packets", "error_resource_cost",
        "work_units", "agent_cpu_seconds", "estimated_state_bytes",
        "run_wall_seconds",
        "mean_cellwise_prediction_mse",
    )
    for (condition, inflow_scale), condition_rows in sorted(groups.items()):
        label = f"{condition}:inflow_scale={inflow_scale:.1f}"
        summaries[label] = {
            "runs": len(condition_rows),
            "extinctions": sum(row["extinct_at_step"] is not None for row in condition_rows),
            **{field: _mean_sd([row[field] for row in condition_rows]) for field in fields},
        }

    paired = {}
    for inflow_scale in sorted({scale for _, scale in groups}):
        selected = groups.get(("selected", inflow_scale), [])
        for control_name in ("neutral_mu_0.05", "neutral_mu_0.15"):
            control = groups.get((control_name, inflow_scale), [])
            key = f"inflow_scale={inflow_scale:.1f}:selected_vs_{control_name}"
            paired[key] = {
                "current_source_share": _paired(
                    selected, control, "mean_post_shift_active_source_edge_share_100_300"
                ),
                "current_source_resource_mass_share": _paired(
                    selected, control,
                    "mean_post_shift_active_source_resource_mass_share_100_300"
                ),
                "target_mse": _paired(selected, control, "mean_target_mse"),
                "cellwise_prediction_mse": _paired(
                    selected, control, "mean_cellwise_prediction_mse"
                ),
                "adaptation_steps": _paired(
                    selected, control, "mean_adaptation_steps_after_change"
                ),
                "return_forgetting_mse": _paired(
                    selected, control, "mean_return_forgetting_mse"
                ),
            }

    result = {
        "hypothesis_id": "H003",
        "analysis": "paired H003 resource-flux populations on the shared SensorStream benchmark",
        "input_result": str(input_path),
        "environment_divergence": {
            "theory": "three IID fair source channels, target XOR noise 0.08, schedule 0,1,2,0 with 600 samples per phase",
            "stage1": "eight rhythm-modulated channels, default target flip 0.10, schedule A,B,A,C,B,A with 1,000 samples per phase; the agent receives no regime/source label",
            "mechanism": "local Beta-Bernoulli prediction, resource packet allocation, local error dissipation, mass death/fission and birth mutation follow THEORY.md",
        },
        "groups": summaries,
        "paired_comparisons": paired,
        "runs": rows,
    }
    if output_dir is not None:
        directory = Path(output_dir)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "analysis.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="stream_bench result.json")
    parser.add_argument("--output", default="experiments/h003-resource-flux-stage1")
    args = parser.parse_args()
    result = analyze(args.input, args.output)
    print(json.dumps({
        "output": str(Path(args.output) / "analysis.json"),
        "groups": result["groups"],
        "paired_comparisons": {
            key: {
                "current_source_share": value["current_source_share"]["mean_selected_minus_control"],
                "current_source_resource_mass_share": value["current_source_resource_mass_share"]["mean_selected_minus_control"],
                "target_mse": value["target_mse"]["mean_selected_minus_control"],
                "cellwise_prediction_mse": value["cellwise_prediction_mse"]["mean_selected_minus_control"],
                "adaptation_steps": value["adaptation_steps"]["mean_selected_minus_control"],
                "return_forgetting_mse": value["return_forgetting_mse"]["mean_selected_minus_control"],
            }
            for key, value in result["paired_comparisons"].items()
        },
    }, sort_keys=True))


if __name__ == "__main__":
    main()
