"""Paired toy: choose the action returning to a predictably controllable state."""
import json
import random
from pathlib import Path


def run(seed, steps=240):
    rng = random.Random(seed)
    # The useful action alternates by world. It reaches a context whose four
    # continuation effects are stable and distinct; the other reaches noise.
    good = seed % 2
    counts = [[0.0] * 4 for _ in range(2)]
    means = [[0.0] * 4 for _ in range(2)]
    errors = [[0.0] * 4 for _ in range(2)]
    successor = [[0, 0] for _ in range(2)]
    chosen = []
    for t in range(steps):
        capacity = []
        for ctx in range(2):
            pairs = [(means[ctx][a], errors[ctx][a]) for a in range(4) if counts[ctx][a] > 1]
            spread = sum((a[0] - b[0]) ** 2 for i, a in enumerate(pairs) for b in pairs[i + 1:])
            noise = sum(p[1] for p in pairs) / max(1, len(pairs))
            capacity.append(spread / (len(pairs) ** 2 * (noise + .1)) if len(pairs) > 1 else 0.0)
        scores = []
        for action in range(2):
            n = sum(successor[action])
            scores.append(sum(successor[action][ctx] * capacity[ctx] for ctx in range(2)) / n if n else 0)
        # Explore one continuation in each reached context, then update from its
        # actually observed effect; paired worlds swap the useful root action.
        action = rng.randrange(2) if t < 40 else max(range(2), key=lambda a: (scores[a], rng.random()))
        chosen.append(action)
        next_state = 1 if action == good else 0
        successor[action][next_state] += 1
        probe = rng.randrange(4)
        value = float(probe) if next_state == 1 else rng.choice((-3.0, 3.0))
        n = counts[next_state][probe]
        old = means[next_state][probe]
        means[next_state][probe] += (value - old) / (n + 1)
        errors[next_state][probe] += ((value - old) ** 2 - errors[next_state][probe]) / (n + 1)
        counts[next_state][probe] += 1
    return sum(a == good for a in chosen[-100:]) / 100


rows = [run(seed) for seed in range(40)]
out = {"paired_worlds": len(rows), "late_correct_action_share": sum(rows) / len(rows),
       "world0": rows[0], "world1": rows[1], "chance": 0.5}
Path(__file__).with_name("returned_control_test_result.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, sort_keys=True))
