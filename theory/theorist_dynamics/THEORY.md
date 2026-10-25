# Dynamics: normalized metabolic credit

## Mechanism

Each organism keeps a local table indexed by the last pursued colour and a
two-state retinal context. The pursued entry receives a decaying eligibility
mass. The delayed change in the organism's own energy writes signed evidence to
that same entry. Action selection uses evidence divided by mass, plus current
visual mass. Thus repeated exposure changes confidence while the estimate stays
bounded by an empirical sample average; no world reward or backpropagation is
used.

The candidate implementation is
`candidates/dynamics_energy_ratio/principle_organism.py`; the matched ablation
sets `credit_scale=0` in
`candidates/dynamics_energy_ratio_ablation/principle_organism.py`.

## Prediction and audit

After a reversal, the selected colour should change over a few trace-decay
times, and when the old context returns its old estimate should remain useful.
The effect should weaken when energy is hidden or when credit writing is
ablated. `structure()` reports six table units and twelve local links, below
the 302-unit limit; no state is shared between batch rows.

The mechanism is a constrained instance of an eligibility trace plus a third
factor. Gerstner et al., arXiv:1801.05219, explicitly review that prior art;
the testable addition here is normalization by decaying local trace mass and
using endogenous energy change as the third factor in the organism world.

## Status

The deterministic probe is only an implementation smoke test. Full organism
results must be read from `sandbox/leaderboard.jsonl` and compared with the
matched ablation using confidence intervals and parameter perturbations.
