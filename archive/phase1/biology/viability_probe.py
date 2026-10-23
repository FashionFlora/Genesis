import json
from pathlib import Path


WORLD_EFFECTS = (
    {"act_0": -0.2, "act_1": 0.2},
    {"act_0": 0.2, "act_1": -0.2},
)
PASSIVE_SIGNATURE = (0, 0, 0, 0)
STATE = 0.2
SET_POINT = 0.0
ACTIONS = ("act_0", "act_1")


def distance_after(action, effects):
    return abs(STATE + effects[action] - SET_POINT)


def best_action(effects):
    return min(ACTIONS, key=lambda action: distance_after(action, effects))


passive_signatures = [PASSIVE_SIGNATURE for _ in WORLD_EFFECTS]
passive_choice = ACTIONS[0]
passive_correct = sum(passive_choice == best_action(effects) for effects in WORLD_EFFECTS)

intervention_correct = 0
estimated_effects = []
for effects in WORLD_EFFECTS:
    estimates = {action: effects[action] for action in ACTIONS}
    estimated_effects.append(estimates)
    intervention_correct += best_action(estimates) == best_action(effects)

result = {
    "worlds": len(WORLD_EFFECTS),
    "passive_signatures_identical": len(set(passive_signatures)) == 1,
    "passive_correct": passive_correct,
    "passive_accuracy": passive_correct / len(WORLD_EFFECTS),
    "intervention_correct": intervention_correct,
    "intervention_accuracy": intervention_correct / len(WORLD_EFFECTS),
    "effects_by_world": estimated_effects,
}
assert result["passive_signatures_identical"]
assert passive_correct == 1
assert intervention_correct == len(WORLD_EFFECTS)

output = Path(__file__).with_name("viability_probe_result.json")
output.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
