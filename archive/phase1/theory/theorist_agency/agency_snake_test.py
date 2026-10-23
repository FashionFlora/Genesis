"""Local Snake replay for the returned-control agency candidate."""
import importlib.util
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JUDGE = ROOT / "sandbox" / "judge.py"


def load_world():
    source = JUDGE.read_text(encoding="utf-8")
    prefix = source.split("# GPU run serialization.***@***", 1)[0]
    namespace = {"__file__": str(JUDGE), "__name__": "local_judge_prefix"}
    exec(compile(prefix, str(JUDGE), "exec"), namespace)
    return namespace["SnakeWorld"]


def load_system(name):
    path = ROOT / "candidates" / name / "principle.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.System


def play(seed, name, world_class):
    world = world_class(seed)
    system = load_system(name)() if name else None
    rng = random.Random(seed)
    turns = 0
    while turns < 1000 and not world.done:
        observation = world.observe()
        if system:
            system.step(observation)
            action = system.act(observation)
        elif name == "_baseline_snake_wall":
            direction = world.direction
            head_x, head_y = world.body[0]
            moves = ((0, -1), (1, 0), (0, 1), (-1, 0))
            action = direction
            for candidate in (direction, (direction + 1) % 4, (direction - 1) % 4):
                dx, dy = moves[candidate]
                point = (head_x + dx, head_y + dy)
                if (0 <= point[0] < 10 and 0 <= point[1] < 10
                        and point not in world.body[:-1]):
                    action = candidate
                    break
        else:
            action = rng.randrange(4)
        world.step(action)
        turns += 1
    return {"survival_steps": turns, "apples": world.apples,
            "coverage": len(world.visited) / 100}


def main():
    world_class = load_world()
    seeds = (1301, 2027, 4099)
    agents = ("agency_returned_control_field", "_baseline_snake_random",
              "_baseline_snake_wall")
    results = {name: [play(seed, name, world_class) for seed in seeds for _ in range(2)]
               for name in agents}
    summary = {name: {key: sum(row[key] for row in rows) / len(rows)
                      for key in rows[0]} for name, rows in results.items()}
    output = {"seeds": seeds, "episodes_per_seed": 2,
              "summary": summary, "episodes": results}
    target = Path(__file__).with_name("agency_snake_test_result.json")
    target.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
