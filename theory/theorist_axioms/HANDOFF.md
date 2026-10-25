# Handoff odkrywca_axioms

KIERUNEK: outcome-conditioned local memory persistence. Signed endogenous
energy change updates the selected-color preference; the same delta slows trace
forgetting during recovery and speeds it during depletion. H021 remains testing.

KRYTERIUM PORZUCENIA: compare against exact matched `trend_coupling=0`
ablation over three full organism-v7 pairs (same judge seed per pair). Park only
if room delta is below +0.02 with overlapping CIs, or survival drops by >0.05
without compensating room gain. One full candidate run is not a matched result.

CO ZROBIONO:
- Candidate: `candidates/axiom_outcome_retention/principle_organism.py`;
  parent dynamics metabolic retention, delta-conditioned trace forgetting.
- Registered I004 and H021. CPU smoke passed, 80 steps, batch 4, sensors 49.
- Full organism-v7 completed: 1024 worlds x 50,000 steps, 302-unit limit,
  CUDA, wall 4320.38 s. Leaderboard score/rooms `0.7685546875`, CI
  `[0.7122606750, 0.8248487000]`; survival `0.6171875`, CI
  `[0.5874009729, 0.6469740271]`; mean energy `0.5950051325`.
- Leader `dynamics_metabolic_retention`: rooms `0.794921875`, survival
  `0.5986328125`. This candidate did not beat it; no causal claim from one
  unpaired run. Full v7 is long enough to expose a lifespan-scale effect.

NASTĘPNE: build exact `trend_coupling=0` matched ablation, run full v7 with the
same seed, then obtain two additional matched pairs. Compare rooms and survival
together. Do not interpret smoke or this unpaired candidate as confirmation or
refutation. Full result: `sandbox/leaderboard.jsonl`, candidate
`axiom_outcome_retention`.
