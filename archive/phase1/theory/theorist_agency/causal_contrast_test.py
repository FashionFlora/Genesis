"""Probe causal contrast with the candidate's actual action selector."""
import importlib.util
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "candidates/agency_causal_contrast/principle.py"
spec = importlib.util.spec_from_file_location("agency_causal_contrast", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def run(seed, preferred, steps=240):
    rng = random.Random(seed)
    system = module.System()
    root = [0.0] * 12
    obs = root
    choices = []
    for _ in range(steps):
        system.step(root)
        action = system.act(obs)
        choices.append(action)
        if action == preferred:
            effect = [1.0] * 12
        elif action == (preferred + 1) % 4:
            effect = [rng.choice((-2.0, 2.0)) for _ in range(12)]
        else:
            effect = [0.0] * 12
        system.step(effect)
        obs = root
    return sum(action == preferred for action in choices[-100:]) / 100.0


rows = [run(seed, seed % 4) for seed in range(40)]
result = {"paired_worlds": len(rows), "late_best_action_share": sum(rows) / len(rows),
          "chance": 0.25, "world0": rows[0], "world1": rows[1]}
target = Path(__file__).with_name("causal_contrast_test_result.json")
target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
