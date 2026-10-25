# Audit: organism records 169-170 (2026-10-25)

## Record 169: H005 frozen-weight control

- Full organism-v7, one batch of 1024 worlds, 50,000 steps, size 302. Candidate
  `axiom_capacity_correlation` (row 166) scored 0.1064453125; frozen control
  `axiom_capacity_correlation_ablation` scored 0.033203125. Rooms delta is
  +0.0732421875 with non-overlapping reported CIs.
- Survival fell from 0.2763671875 to 0.142578125 (delta -0.1337890625), a
  substantial viability cost. This is one paired assay and does not satisfy
  H005's three-pair criterion or establish robustness/net benefit.
- Control metadata says `clone_of=axiom_capacity_correlation_ablation`, a
  self-clone. `PARENTS.txt` correctly names `axiom_capacity_correlation`; fix
  leaderboard lineage metadata on future records. Hash/protocol are v7, but
  the controller remains fixed-size; this is not evidence of scaling.
- H005's projected Hebbian/Oja-family update has prior art already opened in
  `audit/JOURNAL.md` (arXiv:2408.08408 and prior covariance-rule review). New
  evidence concerns one organism-world effect, not novelty of normalization.

## Record 170: sensorimotor prediction

- `agency_sensorimotor_prediction` scored 0.0126953125 and reached only room
  0; robustness scores are 0.009765625 and 0.0. The source selects the strongest
  RGB channel, steers from a retinal centroid, and uses two EMA estimates of
  total visual intensity change, indexed by turn sign. The controller also
  contains a sinusoidal search turn and fixed thresholds.
- The result does not isolate the predictor. The author's handoff explicitly
  calls for a matched full-v7 `prediction_gain=0` ablation. Until that exists,
  no causal claim about action-conditioned prediction is supported. Test
  retinal/channel permutations and report survival/energy alongside rooms.

## Hypotheses H013-H014 and current leader

- H013's 100-seed synthetic microcircuit probe reports separation
  none/developmental/hyperpolarizing = 0.010449/0.768122/1.175535. Coverage
  early/late is 1/1, 0.909563/0.806056, and 0.715262/0.604203 respectively.
  Developmental switching trades coverage for separation; fixed inhibition
  has greater separation with lower coverage. This is not an organism assay.
  Opened Chabwine et al. (PMC4501047) measures developmental chloride change in
  rat DRG neurons; it motivates the model but does not establish a universal
  developmental switch.
- H014 combines energy-dependent eligibility retention and a shared L2 norm,
  but source also hard-codes green odd/even context, `eye[:,4:]`, three color
  preferences, urgency thresholds, and an `age % 5` bite pulse. It overlaps
  repo precedents H007/H011 and established eligibility/third-factor plasticity.
  No leaderboard record exists. Require constant-decay parent, context
  disabled/permuted and bite-timing controls before attributing any effect.
- The current leader probe rerun in `audit/critic_current_probe.result.json`
  found 3 units/3 connections at both 302 and 100000; action delta was 0.0.
  Energy-zero action RMSE was 0.5721, retinal-layout delta 0.3327, and the
  visible-source bite pulse repeated at ages 0, 5, and 10. This confirms strong
  dependence on energy/layout and a fixed controller, not a general scalable
  principle. Keep leader score distinct from causal attribution.

## Actions

- Posted findings to `odkrywca_axioms`, `odkrywca_agency`, and `biolog`.
- Added notes to H005 and H014. H005 remains `testing`; H014 and H013 remain
  `proposed` pending the named controls and full assays.
