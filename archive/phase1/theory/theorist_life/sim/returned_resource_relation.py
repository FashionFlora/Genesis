"""Paired ecology test: relation-local returned flow versus local Hebb."""
import json
import random
from pathlib import Path
from statistics import mean


def run(seed, local, steps=2400, segment=300, sources=8, flip=0.08):
    rng = random.Random(seed)
    width = sources + 1
    target = sources
    support = [[0.0] * width for _ in range(width)]
    mass = [[0.0] * width for _ in range(width)]
    prediction = [0.5] * width
    previous = None
    source_previous = None
    chosen_target = None
    selected = []
    errors = []
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
            errors.append((prediction[target] - y) ** 2)
        if previous is not None:
            for source, before in enumerate(previous):
                signed = 2.0 * before - 1.0
                for target, after in enumerate(observation):
                    observed = 2.0 * after - 1.0
                    if local:
                        estimate = 0.5 + 0.5 * support[source][target] * signed
                        mass[source][target] += 1.0 / (1.0 + (estimate - after) ** 2)
                    support[source][target] = (scale * support[source][target] + signed * observed) / (scale + 1.0)
        chosen = []
        for target_index in range(width):
            weights = [mass[source][target_index] * abs(support[source][target_index]) if local else abs(support[source][target_index]) for source in range(width)]
            source = max(range(width), key=weights.__getitem__)
            chosen.append(source)
            prediction[target_index] = 0.5 + 0.5 * support[source][target_index] * (2.0 * observation[source] - 1.0)
        chosen_target = chosen[target]
        previous = observation
    window = [i for i in range(steps) if i % segment >= segment // 3 and i % segment < 2 * segment // 3]
    return {"match": mean(selected[i] for i in window), "mse": mean(errors[i] for i in window)}


def main():
    rows = []
    for seed in range(30):
        returned = run(seed, True, segment=80, flip=0.15)
        hebb = run(seed, False, segment=80, flip=0.15)
        rows.append({"seed": seed, "returned": returned, "hebb": hebb})
    summary = {name: {metric: mean(row[name][metric] for row in rows) for metric in ("match", "mse")} for name in ("returned", "hebb")}
    result = {"parameters": {"seeds": 30, "steps": 2400, "sources": 8, "segment": 80, "flip": 0.15, "window": "middle third"}, "summary": summary, "paired": rows}
    path = Path(__file__).with_name("returned_resource_relation_results.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
