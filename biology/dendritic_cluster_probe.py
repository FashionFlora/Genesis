#!/usr/bin/env python3
"""Probe branch-local nonlinear integration and persistent coactive clusters.

Inputs are noisy mixtures of recurring feature blocks.  Branches receive the
same number of synapses, use a local threshold, and update only when their
own activity is high.  No labels or reward enter the update; labels are used
only for the held-out nearest-centroid score.
"""
import argparse
import json

import numpy as np


def world(rng, n_blocks=6, width=4):
    dim = n_blocks * width
    # Each class is a pair of blocks; the pair is the latent object.
    protos = np.zeros((n_blocks, dim))
    for k in range(n_blocks):
        protos[k, k * width:(k + 1) * width] = 1.0
        protos[k, ((k + 1) % n_blocks) * width:((k + 2) % n_blocks) * width] = 1.0
    # The final slice above wraps only for the last class; repair it explicitly.
    for k in range(n_blocks):
        protos[k] = 0.0
        protos[k, k * width:(k + 1) * width] = 1.0
        j = (k + 1) % n_blocks
        protos[k, j * width:(j + 1) * width] = 1.0
    return protos


def draw(rng, protos, labels, noise=0.42, gain_jitter=0.12):
    x = protos[np.asarray(labels)].copy()
    x *= 1.0 + gain_jitter * rng.normal(size=(len(labels), 1))
    x += noise * rng.normal(size=x.shape)
    return x


def centroids(z, labels, n_classes):
    return np.asarray([z[np.asarray(labels) == k].mean(0) for k in range(n_classes)])


def accuracy(z, labels, cents):
    d = ((z[:, None, :] - cents[None, :, :]) ** 2).sum(2)
    return float((d.argmin(1) == np.asarray(labels)).mean())


def run(seed, mode, n_train=360, n_test=120, noise=0.42):
    rng = np.random.default_rng(seed)
    protos = world(rng)
    n_classes, dim = protos.shape
    n_branches, width = 6, dim // 6
    labels = np.tile(np.arange(n_classes), n_train // n_classes)
    rng.shuffle(labels)
    train = draw(rng, protos, labels, noise=noise)
    # Novel feature mixtures are presented as a distraction phase.  They share
    # the sensor alphabet but not the old block pairs, so forgetting is visible.
    distractor_protos = (rng.random(size=protos.shape) > 0.72).astype(float)
    distractor = draw(rng, distractor_protos,
                      rng.integers(0, n_classes, len(labels)), noise=noise * 1.15)
    test_labels = np.repeat(np.arange(n_classes), n_test)
    test = draw(rng, protos, test_labels, noise=noise)

    # Spatially clustered blocks versus an equal-size random allocation.
    assignment = np.repeat(np.arange(n_branches), width)
    if mode == "random":
        assignment = assignment[rng.permutation(dim)]
    masks = [np.flatnonzero(assignment == b) for b in range(n_branches)]
    if mode == "global":
        masks = [np.arange(dim)]
        n_branches = 1
    w = 0.25 + 0.03 * rng.normal(size=(n_branches, dim))
    theta = np.full(n_branches, 0.34)
    eta = 0.025

    def encode(x, learn):
        drives = np.asarray([np.mean(x[idx] * w[b, idx]) for b, idx in enumerate(masks)])
        y = np.maximum(drives - theta, 0.0)
        if learn and mode != "fixed":
            # A local branch only captures coactive synapses after its own
            # threshold; this is the digital analogue of branch-local Ca2+.
            active = np.flatnonzero(y > 0.0)
            if len(active):
                for b in active:
                    idx = masks[b]
                    rate = min(y[b], 1.0)
                    w[b, idx] += eta * rate * (x[idx] - w[b, idx])
                # Preserve a finite local resource rather than global growth.
                for b, idx in enumerate(masks):
                    norm = np.linalg.norm(w[b, idx])
                    if norm > 1.25:
                        w[b, idx] *= 1.25 / norm
        return y

    # Re-read the same examples after learning so the reference centroids use
    # the final synapses, rather than a mixture of early and late weights.
    for x in train:
        encode(x, True)
    train_z = np.asarray([encode(x, False) for x in train])
    immediate = centroids(train_z, labels, n_classes)
    old_test_z = np.asarray([encode(x, False) for x in test])
    old_acc_immediate = accuracy(old_test_z, test_labels, immediate)
    # Distractors are experienced without a task signal; the local trace can
    # retain old branches only if the representation is spatially selective.
    for x in distractor:
        encode(x, True)
    after_z = np.asarray([encode(x, False) for x in test])
    old_acc_after = accuracy(after_z, test_labels, immediate)
    retention = float(old_acc_after / max(old_acc_immediate, 1e-9))
    response_change = float(np.mean(np.abs(after_z - old_test_z)))
    return {"seed": seed, "mode": mode, "old_acc_immediate": old_acc_immediate,
            "old_acc_after": old_acc_after, "retention": retention,
            "response_change": response_change}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=200)
    ap.add_argument("--noise", type=float, default=0.42)
    ap.add_argument("--out", default="biology/dendritic_cluster_probe.result.txt")
    args = ap.parse_args()
    modes = ("cluster", "random", "global", "fixed")
    rows = [run(s, m, noise=args.noise) for m in modes for s in range(args.seeds)]
    summary = {}
    for m in modes:
        vals = [r for r in rows if r["mode"] == m]
        summary[m] = {}
        for key in ("old_acc_immediate", "old_acc_after", "retention", "response_change"):
            a = np.asarray([r[key] for r in vals])
            summary[m][key] = {"mean": float(a.mean()), "sd": float(a.std(ddof=1)),
                               "ci95": [float(a.mean() - 1.96 * a.std(ddof=1) / np.sqrt(len(a))),
                                         float(a.mean() + 1.96 * a.std(ddof=1) / np.sqrt(len(a)))]}
    with open(args.out, "w") as f:
        json.dump({"seeds": args.seeds, "noise": args.noise, "summary": summary}, f, indent=2)
        f.write("\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
