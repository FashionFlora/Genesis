"""Independent H001 replication on reward-free sensory event streams."""

import argparse
import json
import os
import statistics
import time

import numpy as np

from stream import SourceNeighborhoodStream
from stream_agents import FixedHebbPredictor, MeanPredictor, ProbationarySproutingPredictor


AGENT_CLASSES = {
    "h001": ProbationarySproutingPredictor,
    "mean": MeanPredictor,
    "fixed_hebb": FixedHebbPredictor,
}


def _mean(values):
    clean = [float(value) for value in values if value is not None]
    return statistics.mean(clean) if clean else None


def _sd(values):
    clean = [float(value) for value in values if value is not None]
    return statistics.stdev(clean) if len(clean) > 1 else (0.0 if clean else None)


def _adaptation_steps(errors, phase_indexes, threshold, window):
    summaries = {}
    for step, phase in enumerate(phase_indexes):
        summaries.setdefault(phase, []).append((step, errors[step]))
    results = {}
    for phase, entries in summaries.items():
        values = [error for _, error in entries]
        found = None
        if len(values) >= window:
            rolling = np.convolve(np.asarray(values), np.ones(window) / window, mode="valid")
            hits = np.flatnonzero(rolling <= threshold)
            if len(hits):
                found = int(hits[0] + window)
        results[phase] = found
    return results


def run_one(agent_name, seed, steps, steps_per_regime, event_rates, null_stream,
            adaptation_window=50, adaptation_threshold=0.16, structure_interval=50,
            target_count=8, regime_count=8, target_sequence=None,
            source_rates=None, target_rates=None):
    agent_class = AGENT_CLASSES[agent_name]
    stream = SourceNeighborhoodStream(
        seed=seed,
        steps_per_regime=steps_per_regime,
        target_count=target_count,
        regime_count=regime_count,
        event_rates=event_rates,
        null_stream=null_stream,
        target_sequence=target_sequence,
        source_rates=source_rates,
        target_rates=target_rates,
    )
    agent = agent_class(input_dim=1, output_dim=target_count, seed=seed)
    supports_stable_contacts = hasattr(agent, "stable")
    online_mse = []
    online_target_mse = []
    phase_indexes = []
    rows = []
    structure_timeline = []
    recovery_by_phase = {}
    phase_streak = 0
    phase_recovered = False
    last_phase = None
    target_hits = 0
    stable_edge_occurrences = 0
    true_edge_occurrences = 0
    stable_steps = 0
    wall_started = time.perf_counter()
    agent_seconds = 0.0

    for step in range(steps):
        source, target_events, meta = stream.sample()
        call_started = time.perf_counter()
        prediction = np.asarray(agent.predict(source), dtype=np.float64)
        agent_seconds += time.perf_counter() - call_started
        if prediction.shape != (target_count,):
            raise ValueError(f"{agent_name}.predict returned shape {prediction.shape}, expected {(target_count,)}")
        error = (prediction - target_events) ** 2
        online_mse.append(float(np.mean(error)))
        if not null_stream:
            online_target_mse.append(float(error[meta["regime"]]))
        phase_indexes.append(meta["phase_index"])

        call_started = time.perf_counter()
        agent.observe(source, target_events)
        agent_seconds += time.perf_counter() - call_started
        structure = agent.structure_metrics()
        stable = getattr(agent, "stable", {})
        is_target_present = (supports_stable_contacts and not null_stream
                             and meta["regime"] in stable)
        if supports_stable_contacts:
            stable_edge_occurrences += len(stable)
        if not null_stream:
            if supports_stable_contacts:
                target_hits += int(is_target_present)
                true_edge_occurrences += sum(target_id == meta["regime"] for target_id in stable)
            if last_phase != meta["phase_index"]:
                phase_streak = 0
                phase_recovered = False
                last_phase = meta["phase_index"]
            if is_target_present:
                phase_streak += 1
            else:
                phase_streak = 0
            if not phase_recovered and phase_streak >= 50:
                recovery_by_phase[meta["phase_index"]] = meta["phase_step"] - 49
                phase_recovered = True

        if supports_stable_contacts:
            stable_steps += int(len(stable) > 0)
        row = {
            "step": step,
            "phase_index": meta["phase_index"],
            "target_regime": None if null_stream else meta["regime"],
            "event_rate": meta["event_rate"],
            "source_rate": meta["source_rate"],
            "background_target_rate": meta["target_rate"],
            "mse": online_mse[-1],
            "target_mse": None if null_stream else online_target_mse[-1],
            "unit_count": structure["unit_count"],
            "connection_count": structure["connection_count"],
            "growth_events": structure["growth_events"],
            "pruning_events": structure["pruning_events"],
        }
        rows.append(row)
        if step % structure_interval == 0 or step == steps - 1:
            structure_timeline.append({"step": step, **structure})

    wall_seconds = time.perf_counter() - wall_started
    structure_final = agent.structure_metrics()
    prediction_adaptation = _adaptation_steps(
        online_target_mse, phase_indexes, adaptation_threshold, adaptation_window
    ) if not null_stream else {}
    prediction_adaptation_values = [value for phase, value in prediction_adaptation.items()
                                    if phase > 0 and value is not None]
    recoveries = list(recovery_by_phase.values())
    return {
        "agent": agent_name,
        "seed": int(seed),
        "condition": "null" if null_stream else "correlated",
        "source_rates": list(stream.source_rates),
        "target_rates": list(stream.target_rates),
        "target_sequence": list(stream.target_sequence),
        "steps": int(steps),
        "mean_online_mse": _mean(online_mse),
        "mean_target_mse": _mean(online_target_mse) if not null_stream else None,
        "target_coverage": (target_hits / steps
                            if supports_stable_contacts and not null_stream else None),
        "stable_edge_precision": (true_edge_occurrences / stable_edge_occurrences
                                  if supports_stable_contacts and not null_stream
                                  and stable_edge_occurrences else None),
        "stable_edges_per_step": (stable_edge_occurrences / steps
                                  if supports_stable_contacts and not null_stream else None),
        "null_stable_edges_per_step": (stable_edge_occurrences / steps
                                       if supports_stable_contacts and null_stream else None),
        "null_fraction_steps_with_stable_edge": (stable_steps / steps
                                                  if supports_stable_contacts and null_stream else None),
        "max_total_contacts": structure_final.get("max_total_contacts", 0),
        "recovery_mean_steps_to_50_sustained": _mean(recoveries),
        "recovery_success_fraction": len(recoveries) / max(1, (steps + steps_per_regime - 1) // steps_per_regime)
            if not null_stream else None,
        "prediction_adaptation_mean_steps": _mean(prediction_adaptation_values),
        "prediction_adaptation_by_phase": {str(k): v for k, v in prediction_adaptation.items()},
        "recovery_by_phase": {str(k): v for k, v in recovery_by_phase.items()},
        "online_mse": [round(value, 6) for value in online_mse],
        "online_target_mse": [round(value, 6) for value in online_target_mse],
        "structure_timeline": structure_timeline,
        "structure_final": structure_final,
        "cost": {
            "wall_seconds": wall_seconds,
            "agent_seconds": agent_seconds,
            "transitions_per_second": steps / max(wall_seconds, 1e-12),
            "reported_work_units": structure_final["work_units"],
            "estimated_state_bytes": structure_final["estimated_state_bytes"],
        },
        "phase_rows": [
            {"phase_index": phase, "steps": sum(r["phase_index"] == phase for r in rows),
             "regime": (rows[next(i for i, r in enumerate(rows) if r["phase_index"] == phase)]["target_regime"]
                        if not null_stream else None),
             "source_rate": rows[next(i for i, r in enumerate(rows) if r["phase_index"] == phase)]["source_rate"],
             "background_target_rate": rows[next(i for i, r in enumerate(rows) if r["phase_index"] == phase)]["background_target_rate"],
             "mean_mse": _mean([r["mse"] for r in rows if r["phase_index"] == phase]),
             "mean_target_mse": _mean([r["target_mse"] for r in rows if r["phase_index"] == phase]),
             "recovery_steps": recovery_by_phase.get(phase)}
            for phase in sorted(set(r["phase_index"] for r in rows))
        ],
    }


def _aggregate(runs):
    keys = ("mean_online_mse", "mean_target_mse", "target_coverage", "stable_edge_precision",
            "stable_edges_per_step", "null_stable_edges_per_step",
            "null_fraction_steps_with_stable_edge", "recovery_mean_steps_to_50_sustained",
            "recovery_success_fraction", "prediction_adaptation_mean_steps")
    output = {}
    groups = sorted({(run["agent"], run["condition"], tuple(run["source_rates"]),
                      tuple(run["target_rates"]), tuple(run["target_sequence"])) for run in runs})
    for agent_name, condition, source_rates, target_rates, target_sequence in groups:
        group = [run for run in runs if run["agent"] == agent_name and run["condition"] == condition
                 and tuple(run["source_rates"]) == source_rates
                 and tuple(run["target_rates"]) == target_rates
                 and tuple(run["target_sequence"]) == target_sequence]
        key = (f"{agent_name}:{condition}:source-rates={','.join(str(x) for x in source_rates)}"
               f":target-rates={','.join(str(x) for x in target_rates)}"
               f":targets={','.join(str(x) for x in target_sequence)}")
        output[key] = {field: {"mean": _mean([run[field] for run in group]),
                               "sd": _sd([run[field] for run in group])}
                       for field in keys}
        output[key]["runs"] = len(group)
        output[key]["max_total_contacts"] = max(run["max_total_contacts"] for run in group)
        output[key]["mean_growth_events"] = _mean([run["structure_final"]["growth_events"] for run in group])
        output[key]["mean_pruning_events"] = _mean([run["structure_final"]["pruning_events"] for run in group])
        output[key]["mean_final_connections"] = _mean([run["structure_final"]["connection_count"] for run in group])
        output[key]["mean_work_units"] = _mean([run["cost"]["reported_work_units"] for run in group])
        output[key]["mean_agent_seconds"] = _mean([run["cost"]["agent_seconds"] for run in group])
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20271022)
    parser.add_argument("--replicates", type=int, default=20)
    parser.add_argument("--steps-per-regime", type=int, default=1500)
    parser.add_argument("--regimes", type=int, default=8)
    parser.add_argument("--target-count", type=int, default=8)
    parser.add_argument("--only-balanced", action="store_true",
                        help="run the fixed-rate target and null conditions only")
    parser.add_argument("--balanced-rate", type=float, default=0.5)
    parser.add_argument("--shift-rates", default="0.1,0.9")
    parser.add_argument("--adaptation-window", type=int, default=50)
    parser.add_argument("--adaptation-threshold", type=float, default=0.16)
    parser.add_argument("--structure-interval", type=int, default=50)
    parser.add_argument("--output", default="experiments/h001-replication")
    args = parser.parse_args()
    if min(args.replicates, args.steps_per_regime, args.regimes, args.target_count) <= 0:
        parser.error("replicates, steps-per-regime, regimes, and target-count must be positive")
    if args.adaptation_window <= 0 or args.structure_interval <= 0:
        parser.error("adaptation-window and structure-interval must be positive")
    shift_rates = tuple(float(value.strip()) for value in args.shift_rates.split(",") if value.strip())
    if not shift_rates or any(not 0.0 < rate < 1.0 for rate in shift_rates):
        parser.error("shift-rates must be comma-separated values strictly between 0 and 1")

    steps = args.steps_per_regime * args.regimes
    seeds = [args.seed + index for index in range(args.replicates)]
    conditions = [
        ("balanced", (args.balanced_rate,), (args.balanced_rate,), False,
         ("h001", "mean", "fixed_hebb"), None),
        ("balanced_null", (args.balanced_rate,), (args.balanced_rate,), True, ("h001",), None),
    ]
    if not args.only_balanced:
        conditions.extend([
            ("joint_target_and_rate_shift", shift_rates, shift_rates, False,
             ("h001", "mean", "fixed_hebb"), None),
            ("joint_target_and_rate_shift_null", shift_rates, shift_rates, True, ("h001",), None),
            ("rate_shift_fixed_target", shift_rates, (args.balanced_rate,), False, ("h001",), (0,)),
            ("rate_shift_fixed_target_null", shift_rates, (args.balanced_rate,), True, ("h001",), (0,)),
        ])
    os.makedirs(args.output, exist_ok=True)
    runs = []
    for condition_name, source_rates, target_rates, null_stream, agents, target_sequence in conditions:
        for replicate_seed in seeds:
            for agent_name in agents:
                run = run_one(agent_name, replicate_seed, steps, args.steps_per_regime,
                              (args.balanced_rate,), null_stream, args.adaptation_window,
                              args.adaptation_threshold, args.structure_interval,
                              target_count=args.target_count, regime_count=args.regimes,
                              target_sequence=target_sequence,
                              source_rates=source_rates, target_rates=target_rates)
                run["condition_name"] = condition_name
                runs.append(run)
    result = {
        "schema_version": "genesis.h001-replication.v1",
        "hypothesis_id": "H001",
        "hypothesis_title": "Coactivity-gated probationary sprouting under a hard synaptic budget",
        "environment": "reward_free_source_neighborhood_events",
        "agent_interface": "predict(source_event)->target_event_probabilities; observe(source_event,target_events)",
        "integrity": {
            "reward_available_to_agent": False,
            "target_regime_available_to_agent": False,
            "event_rate_available_to_agent": False,
            "target_events_are_labels": False,
        },
        "config": {
            "replicates": args.replicates,
            "seeds": seeds,
            "steps_per_regime": args.steps_per_regime,
            "regimes": args.regimes,
            "target_count": args.target_count,
            "steps_per_run": steps,
            "balanced_rate": args.balanced_rate,
            "source_rate_shift_schedule": list(shift_rates),
            "background_target_rate": args.balanced_rate,
            "rate_shift_semantics": "controlled stress condition alternates only source rate while independent background targets stay at balanced_rate and the correlated target copies source; a separate joint condition changes source, background rate, and target identity together",
            "h001_parameters": {
                "N": args.target_count,
                "K_total_including_probe": 2,
                "probe_steps": 50,
                "alpha": 0.02,
                "accept_threshold": 0.08,
                "prune_threshold": 0.025,
                "prune_steps": 100,
                "probe_mode": "coactive",
            },
            "adaptation_window": args.adaptation_window,
            "adaptation_threshold_target_mse": args.adaptation_threshold,
            "structure_interval": args.structure_interval,
            "no_backprop_declared": True,
            "no_reward": True,
        },
        "prediction_definitions": {
            "online_mse": "mean squared error over all eight target event probabilities before observe",
            "target_mse": "MSE on the regime's hidden correlated target channel, omitted for null streams",
            "target_coverage": "fraction of correlated-stream samples where the hidden target is a mature contact; null when the agent exposes no mature-contact state",
            "recovery": "first within-regime step of a 50-sample consecutive run with target as mature contact",
            "null_contacts": "mean mature-contact count per timestep on an independent-target stream",
        },
        "hypothesis_thresholds": {
            "target_coverage_gt": 0.75,
            "mean_recovery_steps_lt": 250,
            "null_stable_contacts_per_step_lt": 0.01,
            "max_total_contacts_lte": 2,
        },
        "hypothesis_thresholds_scope": "registered quantitative prediction is for N=8 and eight regimes; other N values are exploratory extensions",
        "condition_semantics": {
            "balanced": "target_count distinct targets when regimes permits; fixed Bernoulli rate",
            "balanced_null": "independent source/targets, fixed Bernoulli rate",
            "joint_target_and_rate_shift": "target and rate both change each regime; diagnostic only",
            "rate_shift_fixed_target": "target channel 0 stays correlated while source rate alternates and independent background channels remain at balanced_rate",
        },
        "aggregate": _aggregate(runs),
        "runs": runs,
    }
    output_path = os.path.join(args.output, "result.json")
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
    print(json.dumps({"result": output_path, "aggregate": result["aggregate"]}, sort_keys=True))


if __name__ == "__main__":
    main()
