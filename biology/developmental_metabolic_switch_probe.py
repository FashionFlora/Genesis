#!/usr/bin/env python3
"""Age-gated metabolic plasticity with explicit ablations.

The toy organism sees one of three colours in one of two contexts.  A delayed
energy change is the only teaching signal.  The developmental hypothesis is
that early positive plasticity builds a scaffold and mature negative
plasticity removes stale colour/context preferences.
"""
import numpy as np


def run(seed, mode, steps=6000, switch=2400, n_colours=3):
    rng = np.random.default_rng(seed)
    pref = np.zeros((n_colours, 2), dtype=float)
    trace = np.zeros_like(pref)
    previous = (0, 0)
    energy = 0.5
    hits = []
    # Two rooms reverse the useful colour.  Context is visible; energy is not
    # used to choose the right answer, only to update the synaptic trace.
    for t in range(steps):
        context = 0 if (t // 300) % 2 == 0 else 1
        useful = (context + (t // 1800)) % n_colours
        colour = int(rng.integers(n_colours))
        gain = 0.18 if colour == useful else -0.025
        new_energy = np.clip(energy + gain + 0.012 * rng.standard_normal(), 0.0, 1.0)
        delta = np.clip(new_energy - energy, -0.2, 0.2)
        energy = new_energy

        trace *= 0.965
        trace[previous] += 1.0
        if mode == "switch":
            sign = 1.0 if t < switch else -1.0
        elif mode == "ltp":
            sign = 1.0
        elif mode == "ltd":
            sign = -1.0
        else:
            sign = 0.0
        # A shared row-wise budget prevents sign changes from becoming a gain
        # comparison.  This is the digital analogue of synaptic homeostasis.
        pref += sign * 0.018 * delta * trace
        pref -= pref.mean()
        pref = np.clip(pref, -1.5, 1.5)
        chosen = int(np.argmax(pref[:, context]))
        hits.append((chosen, useful, context))
        previous = (colour, context)

    hits = np.asarray(hits)
    windows = []
    for start in (0, 1800, 3600, 5400):
        block = hits[start:start + 600]
        windows.append(float(np.mean(block[:, 0] == block[:, 1])))
    # Held-out room: ask for the current useful colour after the last reversal.
    heldout = []
    for context in (0, 1):
        useful = (context + 3) % n_colours
        heldout.append(int(np.argmax(pref[:, context])) == useful)
    return np.asarray(windows + [np.mean(heldout), np.mean(np.abs(pref))])


def main():
    modes = ("switch", "ltp", "ltd", "none")
    for mode in modes:
        values = np.asarray([run(seed, mode) for seed in range(200)])
        mean = values.mean(axis=0)
        sd = values.std(axis=0)
        print(mode, "window_acc heldout abs_pref",
              *[f"{x:.6f}" for x in mean],
              "sd", *[f"{x:.6f}" for x in sd])
    for switch in (1200, 2400, 3600, 4800):
        values = np.asarray([run(seed, "switch", switch=switch) for seed in range(200)])
        print("switch_age", switch, "mean_window", f"{values[:, :4].mean():.6f}",
              "heldout", f"{values[:, 4].mean():.6f}")


if __name__ == "__main__":
    main()
