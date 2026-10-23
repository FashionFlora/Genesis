"""Independent Snake replication for H062 on held-out seeds."""

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sandbox.judge import SnakeWorld
from candidates.agency_returned_control_field.principle import System


SEEDS = (1327, 2039, 4127)
EPISODES_PER_SEED = 2


def play(seed, agent):
    world = SnakeWorld(seed)
    system = System() if agent == "candidate" else None
    rng = random.Random(seed)
    steps = 0
    while steps < 1000 and not world.done:
        observation = world.observe()
        if agent == "candidate":
            system.step(observation)
            action = system.act(observation)
        elif agent == "wall":
            direction = world.direction
            head_x, head_y = world.body[0]
            moves = ((0, -1), (1, 0), (0, 1), (-1, 0))
            action = direction
            for choice in (direction, (direction + 1) % 4, (direction - 1) % 4):
                dx, dy = moves[choice]
                point = (head_x + dx, head_y + dy)
                if (0 <= point[0] < 10 and 0 <= point[1] < 10
                        and point not in world.body[:-1]):
                    action = choice
                    break
        else:
            action = rng.randrange(4)
        world.step(action)
        steps += 1
    return {"survival_steps": steps, "apples": world.apples,
            "coverage": len(world.visited) / 100}


agents = ("candidate", "random", "wall")
episodes = {
    agent: [play(seed, agent) for seed in SEEDS for _ in range(EPISODES_PER_SEED)]
    for agent in agents
}
summary = {
    agent: {key: sum(row[key] for row in rows) / len(rows)
            for key in rows[0]}
    for agent, rows in episodes.items()
}
result = {"seeds": SEEDS, "episodes_per_seed": EPISODES_PER_SEED,
          "summary": summary, "episodes": episodes}
path = Path(__file__).with_name("eksperymentator_h062_snake_replay.json")
path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, sort_keys=True))
print(f"result={path}")
