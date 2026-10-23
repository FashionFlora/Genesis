"""Check that compact effect closure resolves paired worlds with inverted action value."""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from candidates.action_vector_closure.principle import System


def run(seed, horizon=240):
    rng = random.Random(seed)
    stable = seed % 2
    learner = System()
    baseline = [0.0] * 100
    learner.step(baseline)
    choices = []
    for _ in range(horizon):
        action = learner.act(baseline)
        if action == stable:
            effect = [1.0] * 12
        elif action == (stable + 1) % 4:
            effect = [rng.choice((-2.0, 2.0)) for _ in range(12)]
        else:
            effect = [0.0] * 12
        learner.step(effect + [0.0] * 88)
        learner.step(baseline)
        choices.append(action)
    return sum(action == stable for action in choices[-120:]) / 120.0


rows = [run(seed) for seed in range(40)]
result = {"paired_worlds": len(rows),
          "late_best_action_share": sum(rows) / len(rows),
          "world0_share": rows[0], "world1_share": rows[1]}
Path(__file__).with_name("action_vector_closure_test_result.json").write_text(
    json.dumps(result, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
