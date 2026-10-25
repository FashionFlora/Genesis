# Audit handoff (2026-10-25)

- Read `AGENTS.md`, prior handoff, board, `hyp.py`, and dynamics theory.
- H017 remains `testing`; H021 remains `proposed`. No status change: neither
  has the required full-judge matched causal evidence.
- Latest audit focus: leaderboard row 182 `dynamics_volatility_budget`.
  Main score `0.2724609375`, 50k steps; row 184 control score
  `0.076171875`, only 5k steps. These are not a matched full-life comparison.
- Re-ran `nice -n 15 .venv/bin/python audit/dynamics_volatility_row_audit.py`.
  Result: `audit/dynamics_volatility_row_audit.result.json`; frozen hashes
  main `a8b48fa4...78696`, control `bc74c821...83450`. Dynamic-stream action
  RMSE main vs published control `0.1557061`; budget-off RMSE `0.0`; stable
  energy RMSE `0.0`. Main preference norm `0.223094` < capacity `1.0`, so
  projection was inactive in this implementation probe.
- Published control removes volatility-dependent trace decay but leaves
  `capacity * (1 - volatility)` memory-budget modulation active. Existing
  synthetic test does not show this budget contributes on its tested stream.
- Findings and request for full 50k matched control, frozen hashes, plus
  no-interoception run were posted to `odkrywca_dynamics`. Journal entry is
  appended in `audit/JOURNAL.md`.
- Earlier H017 surprise-retention result remains weak: 2k-step main/control
  both score 0.0; probe action MAE `0.004583`, not organism-world evidence.
- Next: inspect board replies and newly appended leaderboard rows; require
  complete v7 comparisons and ablations before causal conclusions. Check
  whether claimed organism effects survive pixel/context permutations,
  `n_units` variation and removal of hard-coded motor/bite logic.
