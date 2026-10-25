"""Toy check: stochastic identity can make self-avoidance selective.

Branches make a short random walk on a grid.  A contact between branches of
the same cell is removed when their molecular identity sets overlap; contacts
between cells are retained.  This is a mechanism check, not an organism test.
"""

import random


def trial(seed, mode, cells=8, branches=6, steps=30, isoforms=22):
    rng = random.Random(seed)
    # All branches from one cell share its combinatorial molecular code.
    cell_codes = []
    for _ in range(cells):
        if mode == "stochastic":
            cell_codes.append(frozenset(rng.sample(range(isoforms), 4)))
        elif mode == "single":
            cell_codes.append(frozenset((0,)))
        elif mode == "none":
            cell_codes.append(frozenset())
        else:
            raise ValueError(mode)
    labels = []
    for cell in range(cells):
        for _ in range(branches):
            labels.append((cell, cell_codes[cell]))

    paths = []
    for cell, _ in labels:
        x = y = 0
        path = [(x, y)]
        for _ in range(steps):
            dx, dy = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
            x, y = x + dx, y + dy
            path.append((x, y))
        paths.append(path)

    self_contacts = hetero_contacts = 0
    surviving_self = surviving_hetero = 0
    for i in range(len(paths)):
        for j in range(i):
            same_cell = labels[i][0] == labels[j][0]
            overlap = bool(labels[i][1] & labels[j][1])
            contacts = len(set(paths[i]) & set(paths[j]))
            if same_cell:
                self_contacts += contacts
                if not overlap:
                    surviving_self += contacts
            else:
                hetero_contacts += contacts
                if not overlap:
                    surviving_hetero += contacts
    return self_contacts, hetero_contacts, surviving_self, surviving_hetero


def main():
    seeds = range(500)
    print("seeds=500 cells=8 branches_per_cell=6 steps=30 isoforms=22")
    for mode in ("stochastic", "single", "none"):
        rows = [trial(seed, mode) for seed in seeds]
        means = [sum(row[i] for row in rows) / len(rows) for i in range(4)]
        print(
            f"{mode}: raw_self={means[0]:.3f} raw_hetero={means[1]:.3f} "
            f"surviving_self={means[2]:.3f} surviving_hetero={means[3]:.3f}"
        )


if __name__ == "__main__":
    main()
