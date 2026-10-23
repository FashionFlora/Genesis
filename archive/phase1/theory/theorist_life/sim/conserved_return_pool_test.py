"""Paired short-regime source-selection test for conserved returned flow."""
import json
import random
from pathlib import Path
from statistics import mean


def run(seed, conserved, steps=2400, segment=80, sources=8, flip=0.15):
    rng = random.Random(seed)
    width = sources + 1
    support = [[0.0] * width for _ in range(width)]
    mass = [[0.0] * width for _ in range(width)]
    previous = None
    source_previous = None
    prediction = [0.5] * width
    chosen_target = None
    selected, errors = [], []
    scale = 16.0
    schedule = (0, 1, 2, 3, 0, 3, 2, 1)
    for t in range(steps):
        active = schedule[min(t // segment, len(schedule) - 1)]
        x = [rng.randrange(2) for _ in range(sources)]
        y = (source_previous[active] if source_previous is not None else rng.randrange(2)) ^ int(rng.random() < flip)
        observation = x + [y]
        source_previous = x
        if previous is not None:
            selected.append(chosen_target == active)
            errors.append((prediction[-1] - y) ** 2)
            for target, after in enumerate(observation):
                returns = []
                for source, before in enumerate(previous):
                    estimate = 0.5 + 0.5 * support[source][target] * (2 * before - 1)
                    returns.append(1.0 / (1.0 + (estimate - after) ** 2))
                total = sum(returns)
                for source, before in enumerate(previous):
                    cell_x = 2 * before - 1
                    cell_y = 2 * after - 1
                    if conserved:
                        share = returns[source] / total
                        support[source][target] = (scale * support[source][target] + share * cell_x * cell_y) / (scale + share)
                        mass[source][target] = (scale * mass[source][target] + share) / (scale + 1)
                    else:
                        support[source][target] = (scale * support[source][target] + cell_x * cell_y) / (scale + 1)
                        mass[source][target] += returns[source]
        choices = []
        for target in range(width):
            weights = [mass[s][target] * abs(support[s][target]) if conserved else abs(support[s][target]) for s in range(width)]
            source = max(range(width), key=weights.__getitem__)
            choices.append(source)
            prediction[target] = 0.5 + 0.5 * support[source][target] * (2 * observation[source] - 1)
        chosen_target = choices[-1]
        previous = observation
    indices = [i for i in range(steps) if i % segment >= segment // 3 and i % segment < 2 * segment // 3]
    return {"match": mean(selected[i] for i in indices), "mse": mean(errors[i] for i in indices)}


def main():
    rows = [{"seed": seed, "pool": run(seed, True), "hebb": run(seed, False)} for seed in range(30)]
    result = {name: {metric: mean(row[name][metric] for row in rows) for metric in ("match", "mse")}
              for name in ("pool", "hebb")}
    result["paired"] = {metric: mean(row["pool"][metric] - row["hebb"][metric] for row in rows)
                         for metric in ("match", "mse")}
    result["parameters"] = {"seeds": 30, "steps": 2400, "sources": 8, "segment": 80, "flip": 0.15}
    path = Path(__file__).with_name("conserved_return_pool_results.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "paired"}, sort_keys=True))
    print(json.dumps(result["paired"], sort_keys=True))


if __name__ == "__main__":
    main()
