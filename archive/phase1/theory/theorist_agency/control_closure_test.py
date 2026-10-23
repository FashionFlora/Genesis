"""Small intervention test for a consequence-ranked action law."""
import json
import random
from pathlib import Path


def run(best, seed, noise=0.15, horizon=80):
    rng = random.Random(seed)
    means = [0.0, 0.0]
    counts = [0, 0]
    chosen = []
    for t in range(horizon):
        if t < 2:
            action = t
        elif best:
            action = max(range(2), key=lambda a: means[a])
        else:
            action = rng.randrange(2)
        outcome = (0.8 if action == 1 else 0.25) + rng.gauss(0.0, noise)
        counts[action] += 1
        means[action] += (outcome - means[action]) / counts[action]
        chosen.append(action)
    return sum(action == 1 for action in chosen[-40:]) / 40.0


out = {"world": "action 1 has the more repeatable continuation", "noise": 0.15,
       "closure": [], "matched_random": []}
for seed in range(80):
    out["closure"].append(run(True, seed))
    out["matched_random"].append(run(False, seed))
out["closure_mean"] = sum(out["closure"]) / len(out["closure"])
out["random_mean"] = sum(out["matched_random"]) / len(out["matched_random"])
out["difference"] = out["closure_mean"] - out["random_mean"]
path = Path(__file__).with_name("control_closure_test_result.json")
path.write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps({k: out[k] for k in ("closure_mean", "random_mean", "difference")}, sort_keys=True))
