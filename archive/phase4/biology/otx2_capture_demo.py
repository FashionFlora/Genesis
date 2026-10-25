"""Logic check for local versus global capture-gated plasticity.

The capture levels and threshold are invented; this is not a biological fit.
"""


def evaluate(capture, mode, threshold=0.6):
    if mode == "local":
        gates = [level < threshold for level in capture]
    elif mode == "global":
        shared_gate = sum(capture) / len(capture) < threshold
        gates = [shared_gate] * len(capture)
    elif mode == "motif_absent":
        gates = [True] * len(capture)
    else:
        raise ValueError(mode)

    stable_trace_drift = 0.5 if gates[0] else 0.0
    new_module_adaptation = 0.5 if gates[1] else 0.0
    return stable_trace_drift, new_module_adaptation, gates


if __name__ == "__main__":
    capture = (0.9, 0.2)
    print("modules=2 capture=(0.9,0.2) threshold=0.6")
    print("mode | stable_trace_drift | new_module_adaptation | gates")
    for mode in ("local", "global", "motif_absent"):
        drift, adaptation, gates = evaluate(capture, mode)
        print(f"{mode} | {drift:.1f} | {adaptation:.1f} | {gates}")
    print("Interpretation: invented gate logic only; not biology or organism evidence.")
