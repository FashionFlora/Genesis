#!/usr/bin/env python3
"""Toy test of task-gated, young inhibitory units for fine pattern separation.

The learner sees vectors only.  A young inhibitory pool estimates a shared
background direction and suppresses that component; its slow update is gated
by a local engagement flag, not by class labels or reward.  Labels are used
only after the run to measure nearest-centroid separability.
"""
import argparse
import json
import numpy as np


def make_world(rng, dim=24, classes=8):
    common = rng.normal(size=dim)
    common /= np.linalg.norm(common)
    # Class directions share most of their mass, making the fine task hard.
    anchor = rng.normal(size=dim)
    anchor -= common * np.dot(anchor, common)
    anchor /= np.linalg.norm(anchor)
    dirs = []
    for k in range(classes):
        d = anchor + 0.20 * rng.normal(size=dim)
        d -= common * np.dot(d, common)
        d /= np.linalg.norm(d)
        dirs.append(d)
    return common, np.asarray(dirs)


def samples(rng, common, dirs, labels, noise=0.32, common_jitter=0.65):
    out = []
    for y in labels:
        # Variable shared drive is nuisance; class direction is weak.
        x = (1.0 + common_jitter * rng.normal()) * common
        x += 0.55 * dirs[y] + noise * rng.normal(size=common.shape[0])
        out.append(x)
    return np.asarray(out)


def score_nearest(train_r, train_y, test_r, test_y):
    cents = np.asarray([train_r[train_y == k].mean(0) for k in range(8)])
    d = ((test_r[:, None, :] - cents[None, :, :]) ** 2).sum(2)
    return float((d.argmin(1) == test_y).mean())


def run(seed, variant, n_train=80, n_test=160, hard_noise=0.32):
    rng = np.random.default_rng(seed)
    common, dirs = make_world(rng)
    # Easy exposure precedes the fine task, as in the biological experiment.
    easy_y = np.tile(np.arange(8), n_train // 8)
    hard_y = np.tile(np.arange(8), n_train // 8)
    rng.shuffle(easy_y); rng.shuffle(hard_y)
    x_easy = samples(rng, common, dirs, easy_y, noise=0.24, common_jitter=0.35)
    x_hard = samples(rng, common, dirs, hard_y, noise=hard_noise, common_jitter=0.65)
    # Young cells have a plastic estimate of the nuisance direction.
    mu = np.zeros_like(common)
    age = 0.0
    alpha = 0.0 if variant in ("none", "young_off") else 0.42
    if variant == "random":
        mu = rng.normal(size=common.shape[0]); mu /= np.linalg.norm(mu)
    if variant in ("young", "young_off"):
        mu = x_easy.mean(0)
        mu /= max(np.linalg.norm(mu), 1e-9)
    def encode(x, engaged, learn=True):
        nonlocal mu, age
        if variant == "young" and engaged and learn:
            eta = 0.006 * (1.0 - min(age / 2000.0, 0.8))
            mu = (1.0 - eta) * mu + eta * x
            mu /= max(np.linalg.norm(mu), 1e-9)
            age += 1.0
        # Suppression is absent in passive exposure; this is the gate ablation.
        if variant in ("young", "young_off") and not engaged:
            return x
        if alpha == 0.0:
            return x
        proj = np.dot(x, mu)
        return x - alpha * max(0.0, proj) * mu
    # Training representations: easy phase is passive, hard phase is engaged
    # only for the gated young-pool condition.
    r_easy = np.asarray([encode(x, False) for x in x_easy])
    r_hard = np.asarray([encode(x, variant == "young") for x in x_hard])
    test_y = np.repeat(np.arange(8), n_test)
    easy_test_y = np.repeat(np.arange(8), n_test)
    x_easy_test = samples(rng, common, dirs, easy_test_y, noise=0.24, common_jitter=0.35)
    x_test = samples(rng, common, dirs, test_y, noise=hard_noise, common_jitter=0.65)
    r_easy_test = np.asarray([encode(x, False, learn=False) for x in x_easy_test])
    r_test = np.asarray([encode(x, variant == "young", learn=False) for x in x_test])
    hard_acc = score_nearest(r_hard, hard_y, r_test, test_y)
    easy_acc = score_nearest(r_easy, easy_y, r_easy_test, easy_test_y)
    return {"hard_accuracy": hard_acc, "easy_accuracy": easy_acc,
            "background_alignment": float(abs(np.dot(mu, common))),
            "variant": variant, "seed": seed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=200)
    ap.add_argument("--out", default="biology/adultborn_pattern_probe.result.txt")
    ap.add_argument("--noise", type=float, default=0.32)
    args = ap.parse_args()
    variants = ["none", "random", "young_off", "young"]
    rows = []
    for v in variants:
        for s in range(args.seeds):
            row = run(s, v, hard_noise=args.noise)
            rows.append(row)
    summary = {}
    for v in variants:
        a = np.asarray([r["hard_accuracy"] for r in rows if r["variant"] == v])
        e = np.asarray([r["easy_accuracy"] for r in rows if r["variant"] == v])
        summary[v] = {"hard_mean": float(a.mean()), "hard_sd": float(a.std(ddof=1)),
                      "hard_ci95": [float(a.mean() - 1.96*a.std(ddof=1)/np.sqrt(len(a))),
                                    float(a.mean() + 1.96*a.std(ddof=1)/np.sqrt(len(a)))],
                      "easy_mean": float(e.mean())}
    with open(args.out, "w") as f:
        f.write(json.dumps({"seeds": args.seeds, "summary": summary}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
