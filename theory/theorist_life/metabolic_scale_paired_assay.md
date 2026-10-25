# Paired metabolic-scale assay (2026-10-25)

Compared the full organism-v7 records for `life_metabolic_fixed_scale_budget`
and `life_metabolic_adaptive_retention_budget` in
`sandbox/leaderboard.jsonl`. Both ran 1,024 worlds for 50,000 steps at
302-unit capacity. The judge uses world seed 7 for its one batch; retained
per-world samples have matching world-family IDs. The only code change is the
metabolic delta normalizer (`fixed_delta_scale=0.05` versus a decaying online
absolute-delta estimate). All other mechanisms and policy are identical.

Paired fixed-minus-adaptive differences, n=1,024, normal 95% CI from the
per-world difference standard error:

- `rooms_reached`: +0.095703, CI [+0.052685, +0.138721]. Means: fixed
  0.382812, adaptive 0.287109.
- `survival`: -0.041016, CI [-0.069308, -0.012723]. Means: fixed 0.771484,
  adaptive 0.812500.

This is evidence against an adaptive-scale advantage in the tested setting;
the simpler fixed scale improves room reach while costing survival. It is not
a claim that adaptation never helps: only one parameter setting and one
full-judge batch were used, and each world is a single organism-life rather
than an independent replicate of a population. Neither candidate approaches
the 0.8 island leader. The fixed candidate's PARAMS perturbations are also
large and inconsistent, so robustness is unresolved.

Source result records: candidate `life_metabolic_adaptive_retention_budget`
and `life_metabolic_fixed_scale_budget` in `sandbox/leaderboard.jsonl`;
protocol `organism-v7`, `batches=1`, `batch_size=1024`, `steps=50000`.
