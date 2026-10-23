import json
import random
from pathlib import Path


STEPS = 240
SWITCH = 120
WORLDS = 200
NEED_START = 0.5
EFFECT = 0.08
NOISE_SD = 0.02
ACTION_COST = 0.005
GOOD_REPLENISHMENT = 0.006
BAD_SURCHARGE = 0.002


def run(seed, mode):
    rng = random.Random(seed)
    need = NEED_START
    energy = 1.0
    estimate = [0.0, 0.0]
    counts = [0, 0]
    pooled = 0.0
    pooled_count = 0
    support = [0.0, 0.0]
    correct = 0
    post_switch_correct = 0
    recovery = None
    correct_streak = 0
    actions = 0

    for t in range(STEPS):
        orientation = 1 if t < SWITCH else -1
        effects = (-orientation * EFFECT, orientation * EFFECT)
        best = min(range(2), key=lambda a: abs(need + effects[a]))
        if energy < ACTION_COST:
            continue

        if t < 2:
            action = t
        elif mode == "tagged":
            action = min(range(2), key=lambda a: abs(need + estimate[a]))
        elif mode == "pooled":
            action = min(range(2), key=lambda a: abs(need + pooled))
        else:
            action = 0

        correct += action == best
        if t >= SWITCH:
            post_switch_correct += action == best
            correct_streak = correct_streak + 1 if action == best else 0
            if correct_streak == 5 and recovery is None:
                recovery = t - SWITCH - 4

        change = effects[action] + rng.gauss(0.0, NOISE_SD)
        old_need = need
        need = max(-1.0, min(1.0, need + change))
        counts[action] += 1
        estimate[action] += (change - estimate[action]) / min(counts[action], 8)
        pooled_count += 1
        pooled += (change - pooled) / min(pooled_count, 8)

        benefit = abs(old_need) - abs(need)
        support[action] = max(0.0, support[action] + benefit)
        support[1 - action] = max(0.0, support[1 - action] - max(0.0, benefit))
        energy = min(1.0, energy - ACTION_COST + (GOOD_REPLENISHMENT if benefit > 0 else -BAD_SURCHARGE))
        actions += 1

    retained = sum(value > 0.01 for value in support)
    return {
        "accuracy": correct / STEPS,
        "post_switch_accuracy": post_switch_correct / (STEPS - SWITCH),
        "recovery_steps": recovery if recovery is not None else STEPS - SWITCH,
        "energy_remaining": energy,
        "actions": actions,
        "need_abs_final": abs(need),
        "retained_edges": retained,
    }


def main():
    modes = {}
    for mode in ("tagged", "pooled", "fixed"):
        rows = [run(seed, mode) for seed in range(WORLDS)]
        modes[mode] = {key: sum(row[key] for row in rows) / WORLDS for key in rows[0]}
    out = {
        "experiment": "internally motivated action choice with finite energy and unannounced effect reversal",
        "parameters": {"steps": STEPS, "switch": SWITCH, "worlds": WORLDS,
                       "need_start": NEED_START, "effect": EFFECT, "noise_sd": NOISE_SD,
                       "action_cost": ACTION_COST, "good_replenishment": GOOD_REPLENISHMENT,
                       "bad_surcharge": BAD_SURCHARGE},
        "modes": modes,
        "limitation": "The scalar need, energy meter, two actions, and reversal are supplied. This toy tests action-conditioned causal credit under a budget; it is not a biological motivation model.",
    }
    path = Path(__file__).with_name("viability_budget_drift_result.json")
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
