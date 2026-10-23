"""Replicate the one-state support rule on returning hidden regimes.

The evaluator metadata is used only for phase summaries.  Agents receive an
observation, predict the next observation, and then observe that next vector.
"""

import json
import os
import sys
import time

import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engine.coactivity_support import SupportAllocationPredictor
from engine.stream import Regime, SensorStream
from engine.stream_agents import FixedHebbPredictor, MeanPredictor


def _regimes(width, pairs, flip_probability=0.10):
    return {
        name: Regime(name, source=source, target=target,
                     flip_probability=flip_probability)
        for name, source, target in pairs
    }


SHORT_PAIRS = [(chr(65 + i), i, width) for i, width in enumerate(range(6, 10))]
SHORT_REGIMES = _regimes(12, SHORT_PAIRS)
SHORT_SCHEDULE = ("A", "B", "C", "D", "A", "D", "C", "B", "A")
LONG_PAIRS = [(chr(65 + i), i, 16 + i) for i in range(8)]
LONG_REGIMES = _regimes(24, LONG_PAIRS)
LONG_SCHEDULE = ("A", "B", "C", "D", "E", "F", "G", "H",
                 "A", "H", "G", "F", "E", "D", "C", "B", "A")
NULL_REGIMES = _regimes(12, SHORT_PAIRS, flip_probability=0.50)


def _mean(values):
    values = [float(value) for value in values if value is not None]
    return float(np.mean(values)) if values else None


def _phase_rows(rows, window=16, threshold=0.18):
    groups = {}
    for row in rows:
        groups.setdefault(row["phase"], []).append(row)
    previous = {}
    result = []
    for phase in sorted(groups):
        values = groups[phase]
        errors = np.asarray([row["target_mse"] for row in values], dtype=float)
        width = min(window, len(errors))
        rolling = np.convolve(errors, np.ones(window) / window, mode="valid") if len(errors) >= window else []
        hits = np.flatnonzero(np.asarray(rolling) <= threshold) if len(rolling) else []
        late = float(np.mean(errors[-width:]))
        early = float(np.mean(errors[:width]))
        result.append({
            "phase": phase,
            "regime": values[0]["regime"],
            "early_target_mse": early,
            "late_target_mse": late,
            "adaptation_steps": int(hits[0] + window) if len(hits) else None,
            "return_forgetting_mse": early - previous[values[0]["regime"]]
            if values[0]["regime"] in previous else None,
            "support_active_source_share": float(np.mean([
                row["active_source_share"] for row in values
            ])),
            "connections_start": values[0]["connections"],
            "connections_end": values[-1]["connections"],
            "growth_events_end": values[-1]["growth_events"],
            "pruning_events_end": values[-1]["pruning_events"],
        })
        previous[values[0]["regime"]] = late
    return result


def _grok_probe(rows, window=16):
    errors = np.asarray([row["target_mse"] for row in rows], dtype=float)
    if len(errors) < 2 * window:
        return {"max_window_drop": None, "drop_step": None,
                "pre_window_mean": None, "post_window_mean": None,
                "plateau_to_jump": False, "late_plateau_to_jump": False}
    means = np.convolve(errors, np.ones(window) / window, mode="valid")
    drops = means[:-window] - means[window:]
    index = int(np.argmax(drops))
    drop = float(drops[index])
    total = len(errors)
    post_mean = float(means[index + window])
    late = bool(drop >= 0.10 and means[index] >= 0.20 and post_mean <= 0.10
                and index + window >= total / 2)
    return {
        "max_window_drop": drop,
        "drop_step": index + window,
        "pre_window_mean": float(means[index]),
        "post_window_mean": post_mean,
        "plateau_to_jump": bool(drop >= 0.10 and means[index] >= 0.20),
        "late_plateau_to_jump": late,
    }


def run_one(seed, suite, name, factory, segment_length):
    if suite == "short" or suite == "null":
        width, regimes, schedule = 12, SHORT_REGIMES, SHORT_SCHEDULE
        if suite == "null":
            regimes = NULL_REGIMES
    else:
        width, regimes, schedule = 24, LONG_REGIMES, LONG_SCHEDULE
    stream = SensorStream(seed=seed, segment_length=segment_length,
                          input_dim=width, output_dim=width,
                          regimes=regimes, schedule=schedule)
    agent = factory(width, seed)
    observation = stream.observation.copy()
    rows = []
    started = time.perf_counter()
    for step in range(segment_length * len(schedule)):
        prediction = np.asarray(agent.predict(observation), dtype=float)
        target, regime, phase = stream.step()
        active_target = regimes[regime].target
        agent.observe(observation, target)
        metrics = agent.structure_metrics()
        source = regimes[regime].source
        masses = metrics.get("source_support_mass", [])
        active_share = (float(agent.support[source, active_target])
                        / max(1.0, float(agent.budget_units))
                        if hasattr(agent, "support") else 0.0)
        rows.append({
            "step": step,
            "phase": phase,
            "regime": regime,
            "mse": float(np.mean((prediction - target) ** 2)),
            "target_mse": float((prediction[active_target] - target[active_target]) ** 2),
            "active_source_share": active_share,
            "connections": int(metrics["connection_count"]),
            "growth_events": int(metrics["growth_events"]),
            "pruning_events": int(metrics["pruning_events"]),
            "support_mass": metrics.get("support_mass"),
            "source_support_mass": masses,
        })
        observation = target
    final = agent.structure_metrics()
    phases = _phase_rows(rows)
    return {
        "suite": suite,
        "agent": name,
        "seed": int(seed),
        "segment_length": segment_length,
        "schedule": list(schedule),
        "mean_mse": float(np.mean([row["mse"] for row in rows])),
        "mean_target_mse": float(np.mean([row["target_mse"] for row in rows])),
        "mean_active_source_support": float(np.mean([
            row["active_source_share"] for row in rows
        ])),
        "mean_adaptation_steps": _mean([
            row["adaptation_steps"] for row in phases
            if row["adaptation_steps"] is not None
        ]),
        "return_forgetting_mse": _mean([
            row["return_forgetting_mse"] for row in phases
            if row["return_forgetting_mse"] is not None
        ]),
        "grok": _grok_probe(rows),
        "phases": phases,
        "structure_final": final,
        "elapsed_seconds": time.perf_counter() - started,
    }


def _factories():
    return {
        "mean": lambda width, seed: MeanPredictor(width, width, seed),
        "fixed_hebb": lambda width, seed: FixedHebbPredictor(width, width, seed),
        "support_b2": lambda width, seed: SupportAllocationPredictor(width, width, seed, budget=2),
        "support_b4": lambda width, seed: SupportAllocationPredictor(width, width, seed, budget=4),
        "support_b8": lambda width, seed: SupportAllocationPredictor(width, width, seed, budget=8),
        "support_fast": lambda width, seed: SupportAllocationPredictor(width, width, seed, budget=4, eta=0.10),
    }


def main():
    output = "experiments/coactivity-support-stage1/result.json"
    os.makedirs(os.path.dirname(output), exist_ok=True)
    factories = _factories()
    runs = []
    for suite, segment in (("short", 192), ("long", 256), ("null", 192)):
        for seed in (1103, 2029, 7919):
            for name, factory in factories.items():
                runs.append(run_one(seed, suite, name, factory, segment))
    aggregates = {}
    for name in factories:
        for suite in ("short", "long", "null"):
            selected = [row for row in runs if row["agent"] == name and row["suite"] == suite]
            aggregates[f"{suite}:{name}"] = {
                "runs": len(selected),
                "mean_mse": float(np.mean([row["mean_mse"] for row in selected])),
                "mean_target_mse": float(np.mean([row["mean_target_mse"] for row in selected])),
                "mean_active_source_support": float(np.mean([
                    row["mean_active_source_support"] for row in selected
                ])),
                "mean_adaptation_steps": _mean([row["mean_adaptation_steps"] for row in selected]),
                "mean_return_forgetting_mse": _mean([row["return_forgetting_mse"] for row in selected]),
                "mean_grok_drop": _mean([row["grok"]["max_window_drop"] for row in selected]),
                "grok_fraction": float(np.mean([row["grok"]["plateau_to_jump"] for row in selected])),
                "late_grok_fraction": float(np.mean([
                    row["grok"]["late_plateau_to_jump"] for row in selected
                ])),
                "mean_connections": float(np.mean([row["structure_final"]["connection_count"] for row in selected])),
                "mean_growth_events": float(np.mean([row["structure_final"]["growth_events"] for row in selected])),
                "mean_pruning_events": float(np.mean([row["structure_final"]["pruning_events"] for row in selected])),
            }
    result = {
        "experiment": "one-state coactivity support on returning hidden regimes",
        "integrity": {
            "reward_available_to_agent": False,
            "regime_metadata_available_to_agent": False,
            "support_is_only_persistent_edge_state": True,
        },
        "definition": {
            "support_update": "project(k + eta*(x*y - mean_target(x*y)) + noise, nonnegative integer budget)",
            "prediction": "one strongest support per output; strength is k/budget",
            "grok_probe": "16-window error drop >= 0.10 from >=0.20 to <=0.10 after half the run",
        },
        "aggregates": aggregates,
        "runs": runs,
    }
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
    print(json.dumps({"output": output, "aggregates": aggregates}, sort_keys=True))


if __name__ == "__main__":
    main()
