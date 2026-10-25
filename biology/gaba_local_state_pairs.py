"""Paired seed deltas for the robustness probe."""
import numpy as np

from gaba_local_state_robustness import SEEDS, score


def report(geometry):
    rows = {}
    for name, mode, load in (
        ("q0", "local", 0.0), ("local", "local", 0.0015),
        ("global", "global", 0.0015), ("none", "none", 0.0),
    ):
        rows[name] = np.asarray([score(s, mode, 120.0, load, geometry)
                                 for s in range(SEEDS)])
    print(geometry)
    for left, right in (("local", "q0"), ("local", "global"),
                        ("local", "none")):
        delta = rows[left] - rows[right]
        mean = delta.mean(axis=0)
        ci = 1.96 * delta.std(axis=0, ddof=1) / np.sqrt(SEEDS)
        print("%s-%s mean=%s ci95=%s" %
              (left, right,
               "/".join("%.6f" % x for x in mean),
               "/".join("%.6f" % x for x in ci)))


if __name__ == "__main__":
    report("block")
    report("diffuse")
