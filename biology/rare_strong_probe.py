#!/usr/bin/env python3
"""Probe whether a sparse set of correlated strong inputs carries selectivity.

The update sees only x and the unit's own activity.  A fixed row budget makes
the top-k operation a local competition, rather than free weight growth.
Labels are used only for held-out selectivity and retention measurements.
"""
import argparse
import json

import numpy as np


def prototypes(rng, n_classes=8, dim=24):
    # Overlapping circular feature bands give each class shared and specific
    # evidence, so a broad dense code and a few strong inputs differ.
    p = np.zeros((n_classes, dim))
    for c in range(n_classes):
        for d in (0, 1, 2, 7, 8):
            p[c, (3 * c + d) % dim] = 1.0
    return p


def draw(rng, p, labels, noise):
    x = p[np.asarray(labels)].copy()
    x += noise * rng.normal(size=x.shape)
    return np.maximum(x, 0.0)


def summary_metric(z, labels, n_classes):
    means = np.asarray([z[np.asarray(labels) == c].mean(0) for c in range(n_classes)])
    # Class selectivity: preferred response over the mean of other classes.
    pref = means.max(0)
    other = (means.sum(0) - pref) / max(n_classes - 1, 1)
    selectivity = float(np.mean(pref / (other + 1e-6)))
    winners = means.argmax(0)
    coverage = float(len(np.unique(winners)) / n_classes)
    return means, selectivity, coverage


def run(seed, mode, n_train=800, n_test=100, noise=0.35):
    rng = np.random.default_rng(seed)
    n_classes, dim, units = 8, 24, 48
    p = prototypes(rng, n_classes, dim)
    labels = rng.integers(0, n_classes, n_train)
    train = draw(rng, p, labels, noise)
    test_labels = np.repeat(np.arange(n_classes), n_test)
    test = draw(rng, p, test_labels, noise)
    distractor_p = prototypes(rng, n_classes, dim)[:, rng.permutation(dim)]
    distractor_labels = rng.integers(0, n_classes, n_train)
    distractor = draw(rng, distractor_p, distractor_labels, noise * 1.15)

    w = np.abs(0.10 + 0.025 * rng.normal(size=(units, dim)))
    budget = np.sum(w, axis=1, keepdims=True)
    theta = np.full(units, 0.22)
    eta = 0.035
    keep = max(1, dim // 4)
    masks = np.ones_like(w, dtype=bool)

    def encode(x, learn):
        nonlocal w, masks
        drive = (w * x[None, :]).sum(1)
        y = np.maximum(drive - theta, 0.0)
        if learn:
            active = y > 0.0
            if mode in ("topk", "random_topk"):
                # Hebbian growth is local; competition preserves each row's
                # finite synaptic resource and leaves only rare strong links.
                w[active] += eta * y[active, None] * x[None, :]
                if mode == "topk":
                    masks = np.zeros_like(w, dtype=bool)
                    inds = np.argpartition(w, -keep, axis=1)[:, -keep:]
                    masks[np.arange(units)[:, None], inds] = True
                    w *= masks
                else:
                    for i in np.flatnonzero(active):
                        inds = rng.choice(dim, keep, replace=False)
                        m = np.zeros(dim, dtype=bool); m[inds] = True
                        w[i, ~m] = 0.0
            elif mode == "dense":
                w[active] += eta * y[active, None] * x[None, :]
            elif mode == "global":
                w[active] += eta * y[active, None] * x[None, :]
                # Same total update budget, but one population-wide divisor.
                scale = budget.sum() / max(w.sum(), 1e-9)
                w *= scale
            w *= budget / np.maximum(w.sum(1, keepdims=True), 1e-9)
        return y

    for x in train:
        encode(x, True)
    train_z = np.asarray([encode(x, False) for x in train])
    cents, _, _ = summary_metric(train_z, labels, n_classes)
    old_z = np.asarray([encode(x, False) for x in test])
    _, old_sel, old_cov = summary_metric(old_z, test_labels, n_classes)
    # A held-out decoder is deliberately frozen while the organism sees a new
    # distribution, exposing whether rare strong edges are stable or overwrite.
    for x in distractor:
        encode(x, True)
    after_z = np.asarray([encode(x, False) for x in test])
    _, after_sel, after_cov = summary_metric(after_z, test_labels, n_classes)
    pred = ((old_z[:, None, :] - cents[None, :, :]) ** 2).sum(2).argmin(1)
    old_acc = float(np.mean(pred == test_labels))
    response_change = float(np.mean(np.abs(after_z - old_z)))
    # Fraction of each unit's mass in its strongest quarter.
    top_mass = np.sort(w, axis=1)[:, -keep:].sum(1) / np.maximum(w.sum(1), 1e-9)
    return {"seed": seed, "mode": mode, "old_selectivity": old_sel,
            "after_selectivity": after_sel, "old_coverage": old_cov,
            "after_coverage": after_cov, "old_acc": old_acc,
            "retention": float(after_sel / max(old_sel, 1e-9)),
            "response_change": response_change, "top_quarter_mass": float(top_mass.mean())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=200)
    ap.add_argument("--noise", type=float, default=0.35)
    ap.add_argument("--out", default="biology/rare_strong_probe.result.txt")
    args = ap.parse_args()
    modes = ("topk", "dense", "global", "random_topk")
    rows = [run(s, m, noise=args.noise) for m in modes for s in range(args.seeds)]
    summary = {}
    for m in modes:
        vals = [r for r in rows if r["mode"] == m]
        summary[m] = {}
        for key in ("old_selectivity", "after_selectivity", "old_coverage",
                    "after_coverage", "old_acc", "retention", "response_change",
                    "top_quarter_mass"):
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
