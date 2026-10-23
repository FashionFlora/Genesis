"""Test whether observed action consequences identify a preferred action."""

import json
import random
from pathlib import Path


def run(world, seed, noise, policy):
    rng = random.Random(seed)
    means = [0.0, 0.0]
    counts = [0, 0]
    correct = []
    for step in range(40):
        if step < 2:
            action = step
        elif policy == "consequence_rank":
            action = max(range(2), key=lambda a: means[a])
        else:
            action = rng.randrange(2)
        outcome = (0.8 if action == world else 0.2) + rng.gauss(0.0, noise)
        counts[action] += 1
        means[action] += (outcome - means[action]) / counts[action]
        correct.append(action == world)
    return sum(correct[-20:]) / 20


out = {"paired_worlds": 200, "probe_actions_per_world": 2,
       "passive_observation_difference": 0, "results": {}}
for noise in (0.0, 0.35, 1.0):
    results = {"consequence_rank": [], "matched_random": []}
    for pair in range(out["paired_worlds"]):
        for world in (0, 1):
            seed = pair * 2 + world
            for policy in results:
                results[policy].append(run(world, seed, noise, policy))
    out["results"][str(noise)] = {
        policy: sum(scores) / len(scores) for policy, scores in results.items()
    }
out["random_baseline_accuracy"] = 0.5
path = Path(__file__).with_name("continuation_test_result.json")
path.write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, sort_keys=True))
