"""Toy logic check for selective, reversible closure of a plasticity window.

The values are arbitrary; this is not a biological fit or organism controller.
"""


def plasticity_open(matrix, capture, motif_present, threshold=0.6):
    captured_stabilizer = matrix * capture if motif_present else 0.0
    return captured_stabilizer < threshold


if __name__ == "__main__":
    cases = (
        ("intact", 1.0, 0.8, True),
        ("matrix_disrupted", 0.25, 0.8, True),
        ("motif_competed", 1.0, 0.8, False),
    )
    for name, matrix, capture, motif in cases:
        state = "open" if plasticity_open(matrix, capture, motif) else "closed"
        print(f"{name}: {state}")
