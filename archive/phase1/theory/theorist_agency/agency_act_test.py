"""Paired intervention world exercising the candidate's actual System.act."""
import importlib.util
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_system():
    path = ROOT / "candidates/agency_returned_control_field/principle.py"
    spec = importlib.util.spec_from_file_location("agency_candidate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.System


ROOT_OBS = [0.0, 0.0, 0.0, 0.0]
CONTEXT_OBS = ([0.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0])


def run(seed, trials=240):
    rng = random.Random(seed)
    system = load_system()()
    good = seed % 2
    choice_log = []
    for trial in range(trials):
        system.step(ROOT_OBS)
        action = system.act(ROOT_OBS)
        choice_log.append(action == good)
        context = 1 if action == good else 0
        system.step(CONTEXT_OBS[context])
        # Probe the reached state with each possible continuation action. Stable,
        # separated effects define returned controllability; the other state is noise.
        for probe in range(4):
            system.last_action = probe
            if context == 1:
                effect = [0.0] * 4
                effect[probe] = float(probe + 1)
            else:
                effect = [rng.choice((-3.0, 3.0)) for _ in range(4)]
            system.step([a + b for a, b in zip(CONTEXT_OBS[context], effect)])
        # Return to a common root observation. The transition under the last probe
        # is intentionally excluded from root transition evidence by resetting context.
    return sum(choice_log[-100:]) / 100


rows = [run(seed) for seed in range(40)]
out = {"paired_worlds": len(rows), "late_correct_action_share": sum(rows) / len(rows),
       "world0": rows[0], "world1": rows[1], "chance": 0.25,
       "note": "System.act emits four actions; only one root action reaches the controllable context."}
ntarget = Path(__file__).with_name("agency_act_test_result.json")
ntarget.write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, sort_keys=True))
