#!/usr/bin/env python3
"""Local use-trace turnover with a matched random-turnover control.

The rule has no labels, reward, global statistic, or prescribed number of
surviving edges.  Each row keeps an exponentially decaying edge-use trace.
Structural turnover events are sampled from the row's local wear; the matched
control performs the same number of replacements but chooses edges uniformly.
This is a mechanistic probe, not an organism-world result.
"""
import argparse
import json

import numpy as np


def prototypes(n_classes=8, dim=24):
    p = np.zeros((n_classes, dim))
    for c in range(n_classes):
        for d in (0, 1, 2, 7, 8):
            p[c, (3 * c + d) % dim] = 1.0
    return p


def draw(rng, p, labels, noise):
    x = p[np.asarray(labels)].copy()
    x += noise * rng.normal(size=x.shape)
    return np.maximum(x, 0.0)


def metric(z, labels, n_classes):
    means = np.asarray([z[np.asarray(labels) == c].mean(0)
                        for c in range(n_classes)])
    pref = means.max(0)
    other = (means.sum(0) - pref) / max(n_classes - 1, 1)
    sel = float(np.mean(pref / (other + 1e-6)))
    coverage = float(len(np.unique(means.argmax(0))) / n_classes)
    return means, sel, coverage


def run(seed, mode, n_train=800, n_test=100, noise=0.35):
    rng = np.random.default_rng(seed)
    n_classes, dim, units = 8, 24, 48
    p = prototypes(n_classes, dim)
    labels = rng.integers(0, n_classes, n_train)
    train = draw(rng, p, labels, noise)
    test_labels = np.repeat(np.arange(n_classes), n_test)
    test = draw(rng, p, test_labels, noise)
    distractor_p = prototypes(n_classes, dim)[:, rng.permutation(dim)]
    distractor = draw(rng, distractor_p,
                      rng.integers(0, n_classes, n_train), noise * 1.15)

    w = np.abs(0.10 + 0.025 * rng.normal(size=(units, dim)))
    budget = np.sum(w, axis=1, keepdims=True)
    use = np.zeros_like(w)
    theta = np.full(units, 0.22)
    eta = 0.035
    use_decay = 0.018
    # Hazard is proportional to local worn mass; it is not a fixed k or
    # top-k operation.  The random condition receives the same event count.
    turnover_rate = 0.002
    turnover_events = 0

    def encode(x, learn):
        nonlocal w, use, turnover_events
        drive = (w * x[None, :]).sum(1)
        y = np.maximum(drive - theta, 0.0)
        if learn:
            active = y > 0.0
            # The trace records local edge use and decays continuously.
            use *= 1.0 - use_decay
            use += y[:, None] * x[None, :]
            for i in np.flatnonzero(active):
                yi = y[i]
                w[i] += eta * yi * (x - yi * w[i] / max(budget[i, 0], 1e-9))
            w = np.maximum(w, 0.0)
            w *= budget / np.maximum(w.sum(1, keepdims=True), 1e-9)

            # Wear is high where an edge carries weight but has little recent
            # local use.  Both turnover modes share the sampled event count.
            use_norm = use / (use.max(1, keepdims=True) + 1e-6)
            wear = w * (1.0 - use_norm)
            wear_score = wear.mean(1)
            hazards = turnover_rate * wear_score / (wear_score.mean() + 1e-6)
            events = int(rng.poisson(hazards.sum()))
            for _ in range(events):
                i = int(rng.choice(units, p=hazards / max(hazards.sum(), 1e-12)))
                if mode == "trace_turnover":
                    j = int(np.argmin(use[i]))
                elif mode == "random_turnover":
                    j = int(rng.integers(dim))
                else:
                    continue
                w[i, j] = max(1e-4, float(rng.uniform(0.02, 0.12)))
                use[i, j] = 0.0
                turnover_events += 1
            w *= budget / np.maximum(w.sum(1, keepdims=True), 1e-9)
        return y

    for x in train:
        encode(x, True)
    train_z = np.asarray([encode(x, False) for x in train])
    cents, _, _ = metric(train_z, labels, n_classes)
    old_z = np.asarray([encode(x, False) for x in test])
    _, old_sel, old_cov = metric(old_z, test_labels, n_classes)
    old_w = w.copy()
    for x in distractor:
        encode(x, True)
    after_z = np.asarray([encode(x, False) for x in test])
    _, after_sel, after_cov = metric(after_z, test_labels, n_classes)
    pred = ((old_z[:, None, :] - cents[None, :, :]) ** 2).sum(2).argmin(1)
    top = np.sort(w, axis=1)[:, -(dim // 4):].sum(1) / np.maximum(w.sum(1), 1e-9)
    return {"seed": seed, "mode": mode, "old_selectivity": old_sel,
            "after_selectivity": after_sel, "old_coverage": old_cov,
            "after_coverage": after_cov, "old_acc": float(np.mean(pred == test_labels)),
            "retention": float(after_sel / max(old_sel, 1e-9)),
            "response_change": float(np.mean(np.abs(after_z - old_z))),
            "top_quarter_mass": float(top.mean()),
            "turnover_events": turnover_events,
            "weight_drift": float(np.mean(np.abs(w - old_w)))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=200)
    ap.add_argument("--noise", type=float, default=0.35)
    ap.add_argument("--out", default="biology/trace_edge_turnover_probe.result.txt")
    args = ap.parse_args()
    modes = ("oja_local", "trace_turnover", "random_turnover")
    rows = [run(s, m, noise=args.noise) for m in modes for s in range(args.seeds)]
    summary = {}
    for m in modes:
        vals = [r for r in rows if r["mode"] == m]
        summary[m] = {}
        for key in ("old_selectivity", "after_selectivity", "old_coverage",
                    "after_coverage", "old_acc", "retention", "response_change",
                    "top_quarter_mass", "turnover_events", "weight_drift"):
            a = np.asarray([r[key] for r in vals])
            sd = float(a.std(ddof=1))
            mean = float(a.mean())
            summary[m][key] = {"mean": mean, "sd": sd,
                               "ci95": [mean - 1.96 * sd / np.sqrt(len(a)),
                                         mean + 1.96 * sd / np.sqrt(len(a))]}
    with open(args.out, "w") as f:
        json.dump({"seeds": args.seeds, "noise": args.noise, "summary": summary}, f, indent=2)
        f.write("\n")
    for mode, vals in summary.items():
        print(mode, " ".join(f"{k}={v['mean']:.6f}" for k, v in vals.items()))


if __name__ == "__main__":
    main()
