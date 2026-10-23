"""Independent paired replay of returned downstream controllability."""
import json
import random
from pathlib import Path


def run(seed, steps=240):
    rng = random.Random(seed)
    preferred = seed % 2
    counts = [[0] * 4 for _ in range(2)]
    means = [[0.0] * 4 for _ in range(2)]
    errors = [[0.0] * 4 for _ in range(2)]
    transitions = [[0, 0] for _ in range(2)]
    late = []

    for tick in range(steps):
        values = []
        for context in range(2):
            effects = [(means[context][action], errors[context][action])
                       for action in range(4) if counts[context][action] > 1]
            dispersion = sum((left[0] - right[0]) ** 2
                             for index, left in enumerate(effects)
                             for right in effects[index + 1:])
            variance = sum(error for _, error in effects) / max(1, len(effects))
            values.append(dispersion / (len(effects) ** 2 * (variance + 0.1))
                          if len(effects) > 1 else 0.0)

        scores = []
        for action in range(2):
            visits = sum(transitions[action])
            score = (sum(transitions[action][context] * values[context]
                         for context in range(2)) / visits if visits else 0.0)
            scores.append(score)

        choice = (rng.randrange(2) if tick < 40 else
                  max(range(2), key=lambda action: (scores[action], rng.random())))
        destination = int(choice == preferred)
        transitions[choice][destination] += 1
        probe = rng.randrange(4)
        outcome = float(probe) if destination else rng.choice((-3.0, 3.0))
        n = counts[destination][probe]
        residual = outcome - means[destination][probe]
        means[destination][probe] += residual / (n + 1)
        errors[destination][probe] += (residual * residual - errors[destination][probe]) / (n + 1)
        counts[destination][probe] += 1
        if tick >= steps - 100:
            late.append(choice == preferred)

    return sum(late) / len(late)


scores = [run(seed) for seed in range(1000, 1040)]
result = {"paired_worlds": len(scores), "late_correct_action_share": sum(scores) / len(scores),
          "world0": scores[0], "world1": scores[1], "chance": 0.5}
path = Path(__file__).with_suffix(".json")
path.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
