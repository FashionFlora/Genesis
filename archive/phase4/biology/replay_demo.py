"""Toy test: replay can offset passive decay of a learned transition sequence."""


def run(replay: bool) -> tuple[float, float]:
    edges = [1.0] * 5
    for step in range(20):
        edges = [weight * 0.9 for weight in edges]
        if replay and step % 4 == 3:
            edges = [min(1.0, weight + 0.2) for weight in edges]
    return sum(edges) / len(edges), min(edges)


for enabled in (False, True):
    mean, weakest = run(enabled)
    label = "replay" if enabled else "no_replay"
    print(f"{label}: mean_transition={mean:.3f}; weakest={weakest:.3f}")
