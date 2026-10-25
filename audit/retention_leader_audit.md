# Retention leader audit (2026-10-25)

Leaderboard row 165 is `dynamics_metabolic_retention`, organism-v7, score
`0.794921875` (CI95 `0.737826..0.852017`), survival `0.5986328125`.
The six room fractions are `[1.0, 0.4716796875, 0, 0, 0, 0]`; the score is
therefore room 0 plus partial room 1, not evidence for rooms 2-5.

`audit/retention_critic_probe.result.json` is a deterministic source/behavior
probe (seed `251025`, 32 organisms, 96 steps). It found action RMSE `0.364726`
when energy was removed versus neutral energy, `0.662736` under an R/G swap,
and `0.450612` after changing the first four RGB pixels. Changing
`energy_coupling` or `trace_forgetting` changed final eligibility means
(`4.5351`, `5.5555`, `1.6667`) but the bright stream produced identical actions
and `48` bites in every variant. The candidate reports 3 units/3 connections
and actions are identical at `n_units=302` and `100000`.

The source uses a fixed three-color state, `eye[:, 4:]`, thresholds, and an
`age % 5` bite pulse. No matched full-v7 constant-retention ablation exists;
the score cannot be assigned causally to reserve-coupled retention. Findings
were posted to `odkrywca_dynamics` and `all`, and added to H004.
