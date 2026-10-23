#!/usr/bin/env python3
"""Variable-delay action credit with a local persistence (edge) trace.

This is an identifiability toy: the action effects, delay distribution and
regime switch are supplied.  It tests whether a time-distributed eligibility
trace avoids the stale-credit failure of a single fixed lag.
"""
import json
import math
import random
from pathlib import Path

WORLDS = 300
STEPS = 360
SWITCH = 180
MIN_DELAY = 1
MAX_DELAY = 8
NOISE = 0.10
EXPLORATION = 0.20
LEARNING_RATE = 0.12
SUPPORT_RATE = 0.06
EDGE_FLOOR = 0.08
FIXED_LAG = 4
TRACE_TAU = 2.0
TRACE_MAX_AGE = 12


def run(seed, mode, trace_tau=TRACE_TAU):
    rng = random.Random(seed)
    effects = [1.0, -1.0]
    estimates = [0.0, 0.0]
    support = [0.5, 0.5]
    history = []  # (action, age=0 first), retained for trace credit
    pending = [[] for _ in range(MAX_DELAY + 1)]
    correct = 0
    kept = 0
    edge_count = 0

    for t in range(STEPS):
        if t == SWITCH:
            effects = [-x for x in effects]

        if rng.random() < EXPLORATION:
            action = rng.randrange(2)
        else:
            action = min(range(2), key=lambda a: estimates[a])
        history.insert(0, action)
        history = history[:TRACE_MAX_AGE + 1]

        delay = rng.randint(MIN_DELAY, MAX_DELAY)
        observed = effects[action] + rng.gauss(0.0, NOISE)
        due = t + delay
        if due < STEPS:
            pending[due - t].append((action, observed, t))

        feedback = pending.pop(0)
        pending.append([])
        for tagged, outcome, issued_at in feedback:
            if mode == "tagged":
                weights = {tagged: 1.0}
            elif mode == "fixed_lag":
                lagged = history[FIXED_LAG] if len(history) > FIXED_LAG else None
                weights = {} if lagged is None else {lagged: 1.0}
            elif mode == "current":
                weights = {action: 1.0}
            elif mode == "trace":
                raw = {a: 0.0 for a in range(2)}
                for age, prior in enumerate(history):
                    raw[prior] += math.exp(-age / trace_tau)
                total = sum(raw.values())
                weights = {a: value / total for a, value in raw.items()}
            else:
                raise ValueError(mode)

            for credited, weight in weights.items():
                estimates[credited] += LEARNING_RATE * weight * (outcome - estimates[credited])
                # Persistence rises only for a predicted beneficial consequence;
                # the fixed total support makes competition explicit.
                delta = SUPPORT_RATE * weight * (0.5 if outcome < 0 else -0.5)
                support[credited] = max(0.0, support[credited] + delta)
                other = 1 - credited
                support[other] = max(0.0, support[other] - delta)
            total = sum(support)
            if total == 0:
                support = [0.5, 0.5]
            else:
                support = [value / total for value in support]

        if t >= SWITCH + MAX_DELAY:
            correct += action == 0  # action 0 is beneficial after reversal
            kept += support[0] > support[1]
            edge_count += sum(value >= EDGE_FLOOR for value in support)

    scored = STEPS - SWITCH - MAX_DELAY
    return correct / scored, kept / scored, edge_count / scored


def main():
    rows = []
    modes = [("tagged", None), ("trace", 0.5), ("trace", 2.0),
             ("trace", 4.0), ("trace", 8.0), ("fixed_lag", None),
             ("current", None)]
    for mode, trace_tau in modes:
        values = [run(seed, mode, trace_tau or TRACE_TAU) for seed in range(WORLDS)]
        rows.append({
            "mode": mode if trace_tau is None else f"trace_tau_{trace_tau:g}",
            "trace_tau": trace_tau,
            "post_switch_correct_choice": sum(v[0] for v in values) / WORLDS,
            "correct_edge_retention": sum(v[1] for v in values) / WORLDS,
            "mean_edges_above_floor": sum(v[2] for v in values) / WORLDS,
        })
    result = {
        "worlds": WORLDS,
        "steps": STEPS,
        "switch_step": SWITCH,
        "delay_range": [MIN_DELAY, MAX_DELAY],
        "noise_sd": NOISE,
        "exploration_probability": EXPLORATION,
        "fixed_lag": FIXED_LAG,
        "trace_tau": TRACE_TAU,
        "trace_max_age": TRACE_MAX_AGE,
        "learning_rate": LEARNING_RATE,
        "support_rate": SUPPORT_RATE,
        "edge_floor": EDGE_FLOOR,
        "rows": rows,
        "limitation": "Synthetic two-action effects, random delays and reversal; no neural physiology, endogenous need, or growth mechanism.",
    }
    path = Path(__file__).with_name("efference_variable_delay_trace_probe_result.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
