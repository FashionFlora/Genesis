"""Probe a burst-timing developmental rule against narrow STDP and rate Hebb.

This is a mechanistic toy model, not an organism candidate. Two input maps
(``eye`` 0/1) emit spatially local bursts. Output cells initially have a small
eye bias and a spatial preference. A broad burst-overlap rule strengthens
coincident input and weakens non-overlapping input; the ablations use a narrow
spike window or ignore timing and use only mean rates.
"""
import numpy as np


def _run(seed, rule, side=8, outputs=8, steps=2400):
    rng = np.random.default_rng(seed)
    n = side * side
    coords = np.stack(np.meshgrid(np.arange(side), np.arange(side), indexing="ij"), -1).reshape(-1, 2)
    out_pos = np.linspace(0, side - 1, outputs)
    # Two retinas/maps, each with a weak random eye bias and local spatial bias.
    w = rng.uniform(0.20, 0.30, (outputs, 2, n))
    w += rng.normal(0.0, 0.012, w.shape)
    w[:, 0] *= 1.08
    w[:, 1] *= 0.92
    initial_norm = w.sum((1, 2))
    normalized = rule.endswith("_norm")
    base_rule = rule.removesuffix("_norm")
    rates = np.zeros((outputs, 2))
    pre_trace = np.zeros((2, n))
    post_trace = np.zeros(outputs)

    for t in range(steps):
        eye = int(rng.integers(0, 2))
        center = np.array([rng.integers(0, side), rng.integers(0, side)])
        dist2 = np.sum((coords - center) ** 2, axis=1)
        pre = np.exp(-dist2 / 3.0) * (rng.random(n) > 0.18)
        # A burst drives output cells; a brief threshold gives a binary burst.
        drive = (w[:, eye] @ pre) / np.sqrt(n)
        post = (drive > np.quantile(drive, 0.60)).astype(float)
        rates[:, eye] = 0.97 * rates[:, eye] + 0.03 * (drive > 0.11)

        if base_rule == "btdp":
            # Seconds-scale burst memory: current input overlaps the recent
            # postsynaptic burst trace, while unpaired input is mildly pruned.
            eta = 0.018
            coincidence = pre[None, :] * (0.55 * post_trace[:, None] + 0.45 * post[:, None])
            depression = pre[None, :] * (1.0 - post_trace[:, None])
            delta = eta * (coincidence - 0.20 * depression)
            w[:, eye] *= np.clip(1.0 + delta, 0.985, 1.015)
        elif base_rule == "stdp":
            # Narrow, one-step timing ablation: no accumulated burst trace.
            eta = 0.018
            delta = eta * pre[None, :] * (post[:, None] - 0.20)
            w[:, eye] *= np.clip(1.0 + delta, 0.985, 1.015)
        elif base_rule == "rate":
            # Rate-only ablation: equal mean activity has no spatial timing.
            eta = 0.012
            delta = eta * pre[None, :] * (post.mean() - 0.20)
            w[:, eye] *= np.clip(1.0 + delta, 0.985, 1.015)
        elif base_rule != "none":
            raise ValueError(rule)

        if normalized:
            # A cell-local resource constraint prevents timing plasticity from
            # being mistaken for useful refinement through weight explosion.
            w *= (initial_norm / (w.sum((1, 2)) + 1e-8))[:, None, None]

        pre_trace[eye] = 0.80 * pre_trace[eye] + 0.20 * pre
        post_trace = 0.80 * post_trace + 0.20 * post

    # Eye segregation: winner-take-all margin, and spatial concentration of
    # the winning eye's weights along the first input coordinate.
    eye_margin = np.abs(w[:, 0].sum(1) - w[:, 1].sum(1)) / (w.sum((1, 2)) + 1e-8)
    preferred_eye = np.argmax(w.sum(2), axis=1)
    spatial = w[np.arange(outputs), preferred_eye]
    x_pref = (spatial * coords[:, 0]).sum(1) / (spatial.sum(1) + 1e-8)
    spatial_error = np.mean(np.abs(x_pref - out_pos)) / (side - 1)
    return float(eye_margin.mean()), float(1.0 - spatial_error), float(w.mean())


def main():
    for rule in ("none", "btdp", "btdp_norm", "stdp", "stdp_norm", "rate", "rate_norm"):
        vals = np.array([_run(seed, rule) for seed in range(40)])
        print({
            "rule": rule,
            "eye_margin_mean": round(float(vals[:, 0].mean()), 6),
            "eye_margin_sd": round(float(vals[:, 0].std(ddof=1)), 6),
            "spatial_alignment_mean": round(float(vals[:, 1].mean()), 6),
            "spatial_alignment_sd": round(float(vals[:, 1].std(ddof=1)), 6),
            "mean_weight": round(float(vals[:, 2].mean()), 6),
        })


if __name__ == "__main__":
    main()
