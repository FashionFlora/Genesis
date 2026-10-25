"""Matched robustness sweep for local activity-dependent shielding.

The imported model is a toy consequence check, not a biological fit.
"""

import adaptive_myelin_demo as demo


def mean_row(budget: float, drift: float, mode: str, seeds=300):
    old_budget, old_drift = demo.MYELIN_BUDGET, demo.DRIFT
    demo.MYELIN_BUDGET, demo.DRIFT = budget, drift
    try:
        rows = [demo.run(seed, mode) for seed in range(seeds)]
    finally:
        demo.MYELIN_BUDGET, demo.DRIFT = old_budget, old_drift
    return tuple(sum(row[i] for row in rows) / len(rows) for i in range(4))


def main():
    print("seeds=300; budgets=0.8,1.6,3.2,6.4; drift=0.003,0.006,0.012")
    print("budget drift mode new_path_mae old_retention initial_accuracy")
    for budget in (0.8, 1.6, 3.2, 6.4):
        for drift in (0.003, 0.006, 0.012):
            for mode in ("local", "global", "none"):
                _, accuracy, new_error, retained = mean_row(budget, drift, mode)
                print(f"{budget:6.2f} {drift:5.3f} {mode:6s} {new_error:.4f} {retained:.4f} {accuracy:.4f}")


if __name__ == "__main__":
    main()
