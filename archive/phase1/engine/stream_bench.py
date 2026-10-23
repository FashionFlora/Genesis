"""Run the first GENESIS ladder rung: nonstationary reward-free prediction."""

import argparse
import importlib
import json
import os
import platform
import sys
import time

import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from stream import SensorStream
from stream_agents import AGENTS


def _phase_summaries(rows, segment_length, window, threshold):
    grouped = {}
    for row in rows:
        grouped.setdefault(row["phase_index"], []).append(row)
    summaries = []
    previous_late = {}
    for phase_index in sorted(grouped):
        phase_rows = grouped[phase_index]
        name = phase_rows[0]["regime"]
        target_errors = [row["target_mse"] for row in phase_rows]
        overall_errors = [row["mse"] for row in phase_rows]
        width = min(window, len(phase_rows))
        early = float(np.mean(target_errors[:width]))
        late = float(np.mean(target_errors[-width:]))
        adaptation_steps = None
        if len(target_errors) >= window:
            rolling = np.convolve(np.asarray(target_errors), np.ones(window) / window, mode="valid")
            hits = np.flatnonzero(rolling <= threshold)
            if len(hits):
                adaptation_steps = int(hits[0] + window)
        prior = previous_late.get(name)
        first_row = phase_rows[0]
        last_row = phase_rows[-1]
        summaries.append({
            "phase_index": phase_index,
            "regime": name,
            "start_step": phase_rows[0]["step"],
            "end_step": phase_rows[-1]["step"],
            "transitions": len(phase_rows),
            "mean_mse": float(np.mean(overall_errors)),
            "mean_target_mse": float(np.mean(target_errors)),
            "early_target_mse": early,
            "late_target_mse": late,
            "adaptation_steps_to_threshold": adaptation_steps,
            "adaptation_threshold_target_mse": threshold,
            "adaptation_window": window,
            "return_forgetting_mse": (early - prior) if prior is not None else None,
            "previous_visit_late_target_mse": prior,
            "units_start": first_row["unit_count"],
            "units_end": last_row["unit_count"],
            "connections_start": first_row["connection_count"],
            "connections_end": last_row["connection_count"],
            "growth_events_end": last_row["growth_events"],
            "pruning_events_end": last_row["pruning_events"],
            "mean_active_source_edge_share": (
                float(np.mean([row["active_source_edge_share"] for row in phase_rows
                               if row["active_source_edge_share"] is not None]))
                if any(row["active_source_edge_share"] is not None for row in phase_rows)
                else None
            ),
            "post_shift_active_source_edge_share_100_300": (
                float(np.mean([
                    row["active_source_edge_share"] for row in phase_rows
                    if row["active_source_edge_share"] is not None
                    and 100 <= row["step"] - phase_index * segment_length <= 300
                ]))
                if phase_index > 0 and any(
                    row["active_source_edge_share"] is not None
                    and 100 <= row["step"] - phase_index * segment_length <= 300
                    for row in phase_rows
                ) else None
            ),
            "mean_active_source_resource_mass_share": (
                float(np.mean([row["active_source_resource_mass_share"] for row in phase_rows
                               if row["active_source_resource_mass_share"] is not None]))
                if any(row["active_source_resource_mass_share"] is not None for row in phase_rows)
                else None
            ),
            "post_shift_active_source_resource_mass_share_100_300": (
                float(np.mean([
                    row["active_source_resource_mass_share"] for row in phase_rows
                    if row["active_source_resource_mass_share"] is not None
                    and 100 <= row["step"] - phase_index * segment_length <= 300
                ]))
                if phase_index > 0 and any(
                    row["active_source_resource_mass_share"] is not None
                    and 100 <= row["step"] - phase_index * segment_length <= 300
                    for row in phase_rows
                ) else None
            ),
        })
        previous_late[name] = late
    return summaries


def run_one(agent_name, seed, steps, segment_length, input_dim=8, output_dim=8,
            adaptation_window=50, adaptation_threshold=0.16, structure_interval=10):
    agent_class = AGENTS.get(agent_name)
    if agent_class is None and ":" in agent_name:
        module_name, class_name = agent_name.rsplit(":", 1)
        agent_class = getattr(importlib.import_module(module_name), class_name)
    if agent_class is None:
        raise ValueError(f"unknown agent {agent_name!r}; choose a built-in name or module:Class")
    stream = SensorStream(seed=seed, segment_length=segment_length,
                          input_dim=input_dim, output_dim=output_dim)
    agent = agent_class(input_dim=input_dim, output_dim=output_dim, seed=seed)
    observation = stream.observation.copy()
    rows = []
    structure_timeline = []
    wall_started = time.perf_counter()
    agent_seconds = 0.0

    for step in range(int(steps)):
        call_started = time.perf_counter()
        prediction = np.asarray(agent.predict(observation), dtype=np.float64)
        agent_seconds += time.perf_counter() - call_started
        if prediction.shape != (output_dim,):
            raise ValueError(f"{agent_name}.predict returned shape {prediction.shape}, expected {(output_dim,)}")
        target, regime_name, phase_index = stream.step()
        error = (prediction - target) ** 2
        call_started = time.perf_counter()
        agent.observe(observation, target)
        agent_seconds += time.perf_counter() - call_started
        metrics = agent.structure_metrics()
        source_counts = metrics.get("source_edge_counts")
        if isinstance(source_counts, (list, tuple)) and len(source_counts) > 0:
            total_source_edges = sum(float(value) for value in source_counts)
            active_source = stream.regimes[regime_name].source
            active_source_edge_share = (
                float(source_counts[active_source]) / total_source_edges
                if total_source_edges > 0 and 0 <= active_source < len(source_counts) else 0.0
            )
        else:
            active_source_edge_share = None
        source_mass = metrics.get("source_resource_mass")
        if isinstance(source_mass, (list, tuple)) and len(source_mass) > 0:
            total_source_mass = sum(float(value) for value in source_mass)
            active_source = stream.regimes[regime_name].source
            active_source_resource_mass_share = (
                float(source_mass[active_source]) / total_source_mass
                if total_source_mass > 0 and 0 <= active_source < len(source_mass) else 0.0
            )
        else:
            active_source_resource_mass_share = None
        row = {
            "step": step,
            "phase_index": phase_index,
            "regime": regime_name,
            "mse": float(np.mean(error)),
            "target_mse": float(error[stream.regimes[regime_name].target]),
            "unit_count": int(metrics["unit_count"]),
            "connection_count": int(metrics["connection_count"]),
            "growth_events": int(metrics["growth_events"]),
            "pruning_events": int(metrics["pruning_events"]),
            # Evaluator-only structural readout; never passed to the agent.
            "active_source_edge_share": active_source_edge_share,
            "active_source_resource_mass_share": active_source_resource_mass_share,
        }
        rows.append(row)
        if step % structure_interval == 0 or step == steps - 1:
            structure_timeline.append({
                "step": step,
                "phase_index": phase_index,
                "regime": regime_name,
                **{key: value for key, value in metrics.items() if key != "work_units"},
            })
        observation = target

    wall_seconds = time.perf_counter() - wall_started
    final_structure = agent.structure_metrics()
    phases = _phase_summaries(rows, segment_length, adaptation_window, adaptation_threshold)
    adaptation_values = [p["adaptation_steps_to_threshold"] for p in phases[1:]
                         if p["adaptation_steps_to_threshold"] is not None]
    forgetting_values = [p["return_forgetting_mse"] for p in phases
                         if p["return_forgetting_mse"] is not None]
    post_shift_edge_shares = [p["post_shift_active_source_edge_share_100_300"]
                              for p in phases
                              if p["post_shift_active_source_edge_share_100_300"] is not None]
    post_shift_mass_shares = [p["post_shift_active_source_resource_mass_share_100_300"]
                              for p in phases
                              if p["post_shift_active_source_resource_mass_share_100_300"] is not None]
    return {
        "agent": agent_name,
        "seed": int(seed),
        "steps": int(steps),
        "mean_online_mse": float(np.mean([row["mse"] for row in rows])),
        "mean_target_mse": float(np.mean([row["target_mse"] for row in rows])),
        "mean_adaptation_steps_after_change": (float(np.mean(adaptation_values))
                                               if adaptation_values else None),
        "mean_return_forgetting_mse": (float(np.mean(forgetting_values))
                                        if forgetting_values else None),
        "mean_post_shift_active_source_edge_share_100_300": (
            float(np.mean(post_shift_edge_shares)) if post_shift_edge_shares else None
        ),
        "mean_post_shift_active_source_resource_mass_share_100_300": (
            float(np.mean(post_shift_mass_shares)) if post_shift_mass_shares else None
        ),
        "phases": phases,
        "online_mse": [row["mse"] for row in rows],
        "online_target_mse": [row["target_mse"] for row in rows],
        "structure_timeline": structure_timeline,
        "structure_final": final_structure,
        "cost": {
            "wall_seconds": wall_seconds,
            "agent_seconds": agent_seconds,
            "transitions_per_second": steps / max(wall_seconds, 1e-12),
            "reported_work_units": int(final_structure["work_units"]),
            "estimated_state_bytes": int(final_structure["estimated_state_bytes"]),
        },
    }


def _aggregate(runs):
    aggregate = {}
    for name in sorted({run["agent"] for run in runs}):
        selected = [run for run in runs if run["agent"] == name]
        fields = ("mean_online_mse", "mean_target_mse", "mean_adaptation_steps_after_change",
                  "mean_return_forgetting_mse", "mean_post_shift_active_source_edge_share_100_300",
                  "mean_post_shift_active_source_resource_mass_share_100_300")
        aggregate[name] = {}
        for field in fields:
            values = [run[field] for run in selected if run[field] is not None]
            aggregate[name][field] = float(np.mean(values)) if values else None
        aggregate[name]["runs"] = len(selected)
        aggregate[name]["mean_growth_events"] = float(np.mean(
            [run["structure_final"]["growth_events"] for run in selected]))
        aggregate[name]["mean_pruning_events"] = float(np.mean(
            [run["structure_final"]["pruning_events"] for run in selected]))
        aggregate[name]["mean_final_units"] = float(np.mean(
            [run["structure_final"]["unit_count"] for run in selected]))
        aggregate[name]["mean_final_connections"] = float(np.mean(
            [run["structure_final"]["connection_count"] for run in selected]))
        aggregate[name]["mean_agent_seconds"] = float(np.mean([run["cost"]["agent_seconds"] for run in selected]))
    return aggregate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agents", default="mean,persistence,fixed_hebb,growing")
    parser.add_argument("--steps", type=int, default=6000)
    parser.add_argument("--segment-length", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20261022)
    parser.add_argument("--replicates", type=int, default=1)
    parser.add_argument("--adaptation-window", type=int, default=50)
    parser.add_argument("--adaptation-threshold", type=float, default=0.16)
    parser.add_argument("--structure-interval", type=int, default=10)
    parser.add_argument("--output", default="experiments/stream-stage1")
    args = parser.parse_args()
    agents = [name.strip() for name in args.agents.split(",") if name.strip()]
    if not agents or args.steps <= 0 or args.replicates <= 0 or args.structure_interval <= 0:
        parser.error("agents, steps, replicates, and structure interval must be positive")
    os.makedirs(args.output, exist_ok=True)
    runs = []
    for replicate in range(args.replicates):
        seed = args.seed + replicate
        for agent_name in agents:
            runs.append(run_one(agent_name, seed, args.steps, args.segment_length,
                                adaptation_window=args.adaptation_window,
                                adaptation_threshold=args.adaptation_threshold,
                                structure_interval=args.structure_interval))
    result = {
        "schema_version": "genesis.stream-bench.v1",
        "environment": "nonstationary_binary_sensory_prediction",
        "reward_free": True,
        "agent_interface": "predict(observation)->prediction; observe(observation,next_observation)",
        "integrity": {
            "reward_available_to_agent": False,
            "regime_metadata_available_to_agent": False,
            "target_is_next_sensory_observation": True,
        },
        "config": {
            "agents": agents,
            "steps_per_run": args.steps,
            "segment_length": args.segment_length,
            "replicates": args.replicates,
            "seeds": [args.seed + i for i in range(args.replicates)],
            "adaptation_window": args.adaptation_window,
            "adaptation_threshold_target_mse": args.adaptation_threshold,
            "structure_interval": args.structure_interval,
            "stream": SensorStream(seed=args.seed, segment_length=args.segment_length).describe(),
            "python": platform.python_version(),
            "numpy": np.__version__,
        },
        "aggregate": _aggregate(runs),
        "runs": runs,
    }
    result_path = os.path.join(args.output, "result.json")
    with open(result_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
    concise = {name: stats for name, stats in result["aggregate"].items()}
    print(json.dumps({"result": result_path, "aggregate": concise}, sort_keys=True))


if __name__ == "__main__":
    main()
