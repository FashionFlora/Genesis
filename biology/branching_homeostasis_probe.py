"""Probe a local branching homeostat inspired by neuronal avalanches.

This is a mechanistic toy model, not an organism-world result. Nodes have a
fixed directed graph and a local excitability (gain). Activity is injected
without reward; after each avalanche, active parents adjust gain toward one
observed child on average. The matched global condition uses one shared gain.
"""
import math
import random
import statistics


def quantile(values, q):
    values = sorted(values)
    if not values:
        return 0.0
    pos = (len(values) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(values[lo])
    return values[lo] + (pos - lo) * (values[hi] - values[lo])


def run(seed, mode, n=256, out_degree=4, avalanches=1600, burn=400,
        base_p=0.24, eta=0.035, layers=16, damage_at=800,
        damage_fraction=0.20, damage_factor=0.50):
    rng = random.Random(seed)
    width = n // layers
    graph = [[] for _ in range(n)]
    for layer in range(layers):
        next_layer = min(layer + 1, layers - 1)
        lo = next_layer * width
        hi = (next_layer + 1) * width
        for node in range(width):
            graph[layer * width + node] = [rng.randrange(lo, hi)
                                           for _ in range(out_degree)]
    gain = [1.0] * n
    global_gain = 1.0
    damaged = set(rng.sample(range(n), int(n * damage_fraction)))
    sizes = []
    ratios = []
    reached = []
    phase_rows = {"pre": [], "post": []}
    phase_counts = {"pre": [0, 0], "post": [0, 0]}

    for av in range(avalanches):
        active = [rng.randrange(width)]
        total = 0
        parent_count = 0
        child_count = 0
        for layer in range(layers - 1):
            if not active:
                break
            nxt = []
            for local_parent in active:
                parent = layer * width + local_parent
                parent_count += 1
                parent_children = 0
                parent_gain = global_gain if mode == "global" else gain[parent]
                damage = damage_factor if av >= damage_at and parent in damaged else 1.0
                p = min(0.98, base_p * parent_gain * damage)
                for child in graph[parent]:
                    if rng.random() < p:
                        nxt.append(child - (layer + 1) * width)
                        parent_children += 1
                child_count += parent_children
                if mode == "local":
                    gain[parent] = min(3.0, max(0.15,
                        gain[parent] * math.exp(eta * (1.0 - parent_children))))
            total += len(active)
            active = nxt

        if parent_count:
            ratios.append(child_count / parent_count)
        sizes.append(total)
        reached.append(total > 10)
        if mode == "global" and parent_count:
            global_gain = min(3.0, max(0.15,
                global_gain * math.exp(eta * (1.0 - child_count / parent_count))))

        phase = "pre" if av < damage_at else "post"
        phase_rows[phase].append(total)
        phase_counts[phase][0] += child_count
        phase_counts[phase][1] += parent_count
    kept = sizes[burn:]
    kept_ratios = ratios[burn:]
    kept_reached = reached[burn:]
    return {
        "branching_mean": statistics.mean(kept_ratios),
        "branching_sd": statistics.pstdev(kept_ratios),
        "size_mean": statistics.mean(kept),
        "size_p95": quantile(kept, 0.95),
        "transmission_gt10": statistics.mean(kept_reached),
        "pre_branching": phase_counts["pre"][0] / phase_counts["pre"][1],
        "post_branching": phase_counts["post"][0] / phase_counts["post"][1],
        "pre_size": statistics.mean(phase_rows["pre"]),
        "post_size": statistics.mean(phase_rows["post"]),
        "gain_mean": statistics.mean(gain),
    }


def summarize(rows):
    keys = rows[0].keys()
    return " ".join(
        f"{key}={statistics.mean(row[key] for row in rows):.6f}"
        for key in keys
    )


if __name__ == "__main__":
    print("mode branching_mean branching_sd size_mean size_p95 transmission_gt10 pre_branching post_branching pre_size post_size gain_mean; 100 seeds")
    for mode in ("none", "global", "local"):
        rows = [run(seed, mode) for seed in range(100)]
        print(mode, summarize(rows))
