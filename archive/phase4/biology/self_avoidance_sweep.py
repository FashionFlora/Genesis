"""Toy sweep of identity-pool and code-size effects on contact selectivity."""

import random


def paths_for_seed(seed, cells=8, branches=6, steps=30):
    rng = random.Random(seed)
    paths = []
    owners = []
    for cell in range(cells):
        for _ in range(branches):
            x = y = 0
            path = {(x, y)}
            for _ in range(steps):
                dx, dy = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
                x, y = x + dx, y + dy
                path.add((x, y))
            paths.append(path)
            owners.append(cell)
    contacts = []
    for i, path in enumerate(paths):
        for j in range(i):
            n = len(path & paths[j])
            if n:
                contacts.append((owners[i], owners[j], n))
    return contacts


def trial(seed, isoforms, code_size, cells=8):
    contacts = paths_for_seed(seed, cells=cells)
    rng = random.Random(seed + 1_000_003)
    codes = [frozenset(rng.sample(range(isoforms), code_size)) for _ in range(cells)]
    raw_self = raw_hetero = surviving_hetero = 0
    for a, b, n in contacts:
        if a == b:
            raw_self += n
        else:
            raw_hetero += n
            if not codes[a] & codes[b]:
                surviving_hetero += n
    return raw_self, raw_hetero, surviving_hetero


def main():
    seeds = range(500)
    print("seeds=500 cells=8 branches=6 steps=30; shared geometry per seed")
    print("isoforms code_size self_contacts hetero_survival_fraction ids_per_cell")
    for isoforms in (4, 8, 16, 22, 44, 58):
        for code_size in (1, 2, 4, 8):
            if code_size > isoforms:
                continue
            rows = [trial(seed, isoforms, code_size) for seed in seeds]
            raw_self = sum(row[0] for row in rows) / len(rows)
            raw_hetero = sum(row[1] for row in rows) / len(rows)
            survive = sum(row[2] for row in rows) / len(rows)
            print(
                f"{isoforms:8d} {code_size:10d} {raw_self:13.3f} "
                f"{survive / raw_hetero:.4f} {code_size:13d}"
            )


if __name__ == "__main__":
    main()
