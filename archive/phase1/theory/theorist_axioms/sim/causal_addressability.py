"""Stream test for the causal-addressability principle.

The proposed invariant is that persistent predictive state is indexed by a
causal address (the target channel and the local rule), rather than pooled into
one trace.  A short-lived posterior chooses the currently useful address, but
the sufficient statistics of old addresses remain available.  A small rule
library is shared across addresses; this tests whether a learned copy/invert
law can be reused at a previously unseen target channel.

This is a stream diagnostic only.  It has no reward, labels, gradients, or
regime metadata in the agent interface.  The pooled control intentionally
collapses all addresses into one signed coincidence accumulator.
"""
from __future__ import annotations

import json
import math
import random
import statistics
from pathlib import Path

SEEDS = tuple(range(40))
CHANNELS = 4
PHASE_LENGTH = 400
SCHEDULE = ((0, "copy"), (1, "copy"), (3, "copy"), (2, "copy"), (0, "copy"))
NOISE = 0.08
RULES = ("copy", "invert")
# The active address is selected from current local evidence. Persistent counts
# provide the memory; the short activation trace handles regime changes.
RHO = 0.20
SUSTAINED = 20


def make_rows(seed: int, null_stream: bool = False):
    rng = random.Random(seed)
    rows = []
    for t in range(PHASE_LENGTH * len(SCHEDULE)):
        x = float(rng.random() < 0.5)
        target, rule = SCHEDULE[t // PHASE_LENGTH]
        ys = [float(rng.random() < 0.5) for _ in range(CHANNELS)]
        if not null_stream:
            expected = x if rule == "copy" else 1.0 - x
            ys[target] = expected if rng.random() >= NOISE else 1.0 - expected
        rows.append((x, ys, None if null_stream else (target, rule)))
    return rows


def sigmoid_weights(logits):
    top = max(logits)
    values = [math.exp(value - top) for value in logits]
    total = sum(values)
    return [value / total for value in values]


def first_sustained(values, target, start, stop, width=SUSTAINED):
    for index in range(start, stop - width + 1):
        if all(value == target for value in values[index:index + width]):
            return index - start
    return stop - start


class AddressedPredictor:
    """Persistent per-address evidence with a shared reusable rule prior."""

    def __init__(self, generalize=True):
        self.generalize = bool(generalize)
        self.logits = [0.0] * (CHANNELS * len(RULES))
        # Fractional Beta counts are responsibilities, not hidden labels.
        self.success = [[0.5, 0.5] for _ in range(CHANNELS)]
        self.total = [[1.0, 1.0] for _ in range(CHANNELS)]
        self.rule_success = [0.5, 0.5]
        self.rule_total = [1.0, 1.0]

    def _p_correct(self, channel, rule):
        # A rule is a reusable causal invariant.  Its global evidence acts as
        # a data-backed prior for a new address, while local evidence remains
        # available to override it when that address has a different future.
        return (self.success[channel][rule] + self.rule_success[rule]) / (
            self.total[channel][rule] + self.rule_total[rule])

    def _rule_prior(self, rule):
        if not self.generalize:
            return 0.5
        return (self.rule_success[rule] + 0.5) / (self.rule_total[rule] + 1.0)

    def _log_likelihood(self, channel, rule, x, ys):
        p = self._p_correct(channel, rule)
        expected = x if rule == 0 else 1.0 - x
        correct = 1.0 if ys[channel] == expected else 0.0
        return math.log(max(p if correct else 1.0 - p, 1e-12))

    def predict(self, x):
        del x
        weights = sigmoid_weights(self.logits)
        prediction = [0.5] * CHANNELS
        for channel in range(CHANNELS):
            for rule in range(len(RULES)):
                index = channel * len(RULES) + rule
                # Prediction is filled in by predict_observation, where x is known.
                del index
        return prediction

    def predict_observation(self, x):
        weights = sigmoid_weights(self.logits)
        prediction = [0.5] * CHANNELS
        for channel in range(CHANNELS):
            for rule in range(len(RULES)):
                index = channel * len(RULES) + rule
                p = self._p_correct(channel, rule)
                expected_one = x if rule == 0 else 1.0 - x
                prediction[channel] += weights[index] * (p * expected_one + (1.0 - p) * (1.0 - expected_one) - 0.5)
        return prediction, weights

    def observe(self, x, ys):
        log_likelihoods = []
        for channel in range(CHANNELS):
            for rule in range(len(RULES)):
                log_likelihoods.append(self._log_likelihood(channel, rule, x, ys))
        mean_ll = statistics.mean(log_likelihoods)
        # Centering makes this a local competition among addresses.  The
        # shared rule prior is a small bias for an unseen address, not a
        # global accumulator that can suppress a contradictory local rule.
        updated = []
        for index, (old, ll) in enumerate(zip(self.logits, log_likelihoods)):
            rule = index % len(RULES)
            updated.append((1.0 - RHO) * old + (
                ll - mean_ll + 0.2 * math.log(self._rule_prior(rule))))
        self.logits = updated
        weights = sigmoid_weights(self.logits)
        for channel in range(CHANNELS):
            for rule in range(len(RULES)):
                index = channel * len(RULES) + rule
                expected = x if rule == 0 else 1.0 - x
                correct = 1.0 if ys[channel] == expected else 0.0
                responsibility = weights[index]
                self.success[channel][rule] += responsibility * correct
                self.total[channel][rule] += responsibility
                self.rule_success[rule] += responsibility * correct
                self.rule_total[rule] += responsibility

    def state_bytes(self):
        return CHANNELS * len(RULES) * (8 * 4) + len(self.logits) * 8


class PooledAccumulator:
    """Control with one unpartitioned signed evidence trace per address."""

    def __init__(self):
        self.scores = [0.0] * (CHANNELS * len(RULES))

    def predict_observation(self, x):
        logits = [abs(score) for score in self.scores]
        weights = sigmoid_weights(logits)
        pred = [0.5] * CHANNELS
        for channel in range(CHANNELS):
            for rule in range(len(RULES)):
                index = channel * len(RULES) + rule
                expected_one = x if rule == 0 else 1.0 - x
                pred[channel] += weights[index] * (expected_one - 0.5)
        return pred, weights

    def observe(self, x, ys):
        for channel in range(CHANNELS):
            for rule in range(len(RULES)):
                expected = x if rule == 0 else 1.0 - x
                correct = 1.0 if ys[channel] == expected else -1.0
                self.scores[channel * len(RULES) + rule] += correct

    def state_bytes(self):
        return len(self.scores) * 8


def run(seed, agent, null_stream=False):
    rows = make_rows(seed, null_stream)
    predictions = []
    chosen = []
    losses = []
    for x, ys, _ in rows:
        pred, weights = agent.predict_observation(x)
        predictions.append(pred)
        choice = max(range(len(weights)), key=weights.__getitem__)
        chosen.append((choice // len(RULES), RULES[choice % len(RULES)]))
        losses.append(sum((p - y) ** 2 for p, y in zip(pred, ys)) / CHANNELS)
        agent.observe(x, ys)

    phases = []
    for phase, (target, rule) in enumerate(SCHEDULE):
        start, stop = phase * PHASE_LENGTH, (phase + 1) * PHASE_LENGTH
        expected = (target, rule)
        phases.append({
            "phase": phase,
            "target": target,
            "rule": rule,
            "target_mse": statistics.mean(
                [(predictions[t][target] - rows[t][1][target]) ** 2 for t in range(start, stop)]
            ) if not null_stream else None,
            "adaptation_steps": first_sustained(chosen, expected, start, stop),
        })
    return {
        "seed": seed,
        "null_stream": null_stream,
        "mean_mse": statistics.mean(losses),
        "phases": phases,
        "chosen": chosen,
        "state_bytes": agent.state_bytes(),
    }


def summarize(rows, key):
    values = [row[key] for row in rows if row[key] is not None]
    return {"mean": statistics.mean(values) if values else None,
            "sd": statistics.pstdev(values) if len(values) > 1 else 0.0 if values else None}


def main():
    addressed = [run(seed, AddressedPredictor(True)) for seed in SEEDS]
    independent = [run(seed, AddressedPredictor(False)) for seed in SEEDS]
    pooled = [run(seed, PooledAccumulator()) for seed in SEEDS]
    null = [run(seed, AddressedPredictor(True), True) for seed in SEEDS]

    def phase_metric(rows, phase, field):
        return [row["phases"][phase][field] for row in rows]

    result = {
        "experiment": "causal addressability: persistent address-indexed predictive state",
        "principle": "retain predictive states separately for distinguishable local futures; reuse a rule prior across addresses",
        "parameters": {
            "seeds": list(SEEDS), "channels": CHANNELS, "phase_length": PHASE_LENGTH,
            "schedule": [list(item) for item in SCHEDULE], "noise": NOISE,
            "rho": RHO, "rules": list(RULES), "sustained_steps": SUSTAINED,
        },
        "addressed": {
            "mean_mse": summarize(addressed, "mean_mse"),
            "state_bytes": addressed[0]["state_bytes"],
            "first_A_steps": summarize([{"v": phase_metric(addressed, 0, "adaptation_steps")[i]} for i in range(len(SEEDS))], "v"),
            "return_A_steps": summarize([{"v": phase_metric(addressed, 4, "adaptation_steps")[i]} for i in range(len(SEEDS))], "v"),
            "heldout_C_steps": summarize([{"v": phase_metric(addressed, 3, "adaptation_steps")[i]} for i in range(len(SEEDS))], "v"),
            "phase_target_mse": [summarize([{"v": row["phases"][phase]["target_mse"]} for row in addressed], "v") for phase in range(len(SCHEDULE))],
        },
        "independent_address_control": {
            "mean_mse": summarize(independent, "mean_mse"),
            "heldout_C_steps": summarize([{"v": phase_metric(independent, 3, "adaptation_steps")[i]} for i in range(len(SEEDS))], "v"),
            "return_A_steps": summarize([{"v": phase_metric(independent, 4, "adaptation_steps")[i]} for i in range(len(SEEDS))], "v"),
        },
        "pooled_control": {
            "mean_mse": summarize(pooled, "mean_mse"),
            "first_A_steps": summarize([{"v": phase_metric(pooled, 0, "adaptation_steps")[i]} for i in range(len(SEEDS))], "v"),
            "return_A_steps": summarize([{"v": phase_metric(pooled, 4, "adaptation_steps")[i]} for i in range(len(SEEDS))], "v"),
        },
        "null_stream": {
            "mean_mse": summarize(null, "mean_mse"),
            "state_bytes": null[0]["state_bytes"],
            "phase_choice_accuracy_like": summarize([{"v": sum(row["chosen"][t] == SCHEDULE[t // PHASE_LENGTH] for t in range(len(row["chosen"]))) / len(row["chosen"])} for row in null], "v"),
        },
        "runs": {"addressed": addressed, "independent": independent, "pooled": pooled, "null": null},
    }
    output = Path(__file__).with_name("causal_addressability_result.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "runs"}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
