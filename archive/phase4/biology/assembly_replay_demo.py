"""Toy ablation of timing-matched replay stabilizing local assemblies.

The source experiment repeatedly evoked hippocampal sharp-wave/ripple-like
patterns.  Here each assembly is a prototype and replay updates only the
prototype selected by the event.  This is a logic check, not an organism
simulation or a fit to the experimental time scale.
"""

import random


DIM = 12
ASSEMBLIES = 4
INITIAL_EVENTS = 8
REPLAY_EVENTS = 100
NOISE = 0.35
RATE = 0.08


def mse(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) / len(a)


def run(seed, mode):
    rng = random.Random(seed)
    targets = []
    for assembly in range(ASSEMBLIES):
        targets.append([
            (1.0 if ((i + 2 * assembly) % ASSEMBLIES == 0) else -1.0)
            + rng.gauss(0.0, 0.12)
            for i in range(DIM)
        ])

    prototypes = [[rng.gauss(0.0, 0.5) for _ in range(DIM)] for _ in targets]
    # Initial exploration creates a weak, noisy trace in each assembly.
    for assembly in range(ASSEMBLIES):
        for _ in range(INITIAL_EVENTS):
            sample = [x + rng.gauss(0.0, NOISE) for x in targets[assembly]]
            prototypes[assembly] = [
                old + RATE * (new - old)
                for old, new in zip(prototypes[assembly], sample)
            ]

    for event in range(REPLAY_EVENTS):
        assembly = event % ASSEMBLIES
        if mode == "shuffled":
            source = rng.randrange(ASSEMBLIES)
        else:
            source = assembly
        sample = [x + rng.gauss(0.0, NOISE) for x in targets[source]]
        if mode == "no_plasticity":
            continue
        if mode == "no_replay":
            continue
        prototypes[assembly] = [
            old + RATE * (new - old)
            for old, new in zip(prototypes[assembly], sample)
        ]

    reconstruction = sum(mse(prototypes[i], targets[i]) for i in range(ASSEMBLIES)) / ASSEMBLIES
    # A probe asks which assembly is closest; this captures cross-talk as well
    # as within-assembly stabilization.
    correct = 0
    for assembly in range(ASSEMBLIES):
        for _ in range(40):
            probe = [x + rng.gauss(0.0, NOISE) for x in targets[assembly]]
            scores = [mse(probe, prototype) for prototype in prototypes]
            correct += int(min(range(ASSEMBLIES), key=scores.__getitem__) == assembly)
    return reconstruction, correct / (ASSEMBLIES * 40)


def main():
    for mode in ("matched", "shuffled", "no_replay", "no_plasticity"):
        rows = [run(seed, mode) for seed in range(500)]
        means = [sum(row[i] for row in rows) / len(rows) for i in range(2)]
        print(f"{mode}: probe_mse={means[0]:.4f}; assembly_accuracy={means[1]:.4f}")


if __name__ == "__main__":
    main()
