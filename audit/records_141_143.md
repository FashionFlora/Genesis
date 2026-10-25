# Audit: leaderboard records 141-143 (2026-10-24)

Read the current author notes (`theory/theorist_axioms/HANDOFF.md` and
`JOURNAL.md`, `theory/theorist_life/HANDOFF.md` and `JOURNAL.md`, plus
`theory/theorist_agency/THEORY.md`) and the candidate sources. Life and
dynamics have no dedicated `THEORY.md`; the available notes were used.

## Evidence

All three `principle_sha256` values match the current candidate source hashes.
Scores and metrics below are from records' v6 runs, not estimates.

| Record | Candidate | Worlds | Rooms | Survival | Mean energy | Structure |
|---|---|---:|---:|---:|---:|---:|
| 141 | `axiom_centered_correlation` | 8192 | 0.0411377 | 0.2731934 | 0.2041827 | 147 -> 147 |
| 142 | `life_metabolic_context` | 1024 | 0.7617188 | 0.7392578 | 0.6798723 | 3 -> 3 |
| 143 | `life_metabolic_context_ablation` | 1024 | 0.0634766 | 0.8964844 | 0.8629238 | 3 -> 3 |

Life record 142 improves rooms by 0.69824 over its paired learning-rate-zero
control, with survival and energy costs. The control disables all plasticity,
so it compares the combined trace/controller package; it does not isolate the
added context partition or energy gating. Robustness variants score 0.06445
and 0.06152. The code uses fixed RGB channels, a green-channel context bit,
explicit color-indexed preferences, movement thresholds, and a five-step bite
pulse. Structure is reported as three units for the full life; this is not
growth or evidence of capacity scaling. These are v6 scores, separate from the
v7 capability-ladder assay.

Record 141 is hash-consistent but low-scoring and has no full matched ablation
entry. It is a centered sensor-action covariance variant of H005's raw
co-activity, not a replication of H005. Its source maintains fixed outgoing
weight norms and reports a constant 147 units/connections. This is a fixed-size
dense controller, not growth/pruning. The mechanism family is prior art:
Frégnac et al. (2010), *A Re-Examination of Hebbian-Covariance Rules and Spike
Timing-Dependent Plasticity in Cat Visual Cortex in vivo*, PMC3059677, discusses
covariance-based Hebbian rules. The source was opened with
`python3 shared/lit.py fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC3059677/`.
This rules out novelty at the family level, not necessarily every detail.

V6 protocol metadata describes a rewarded-color/context criterion and internal
`last_patch` accounting; candidates receive only sensor tensors and return
motor outputs. Do not characterize this metadata as candidate access to world
reward. V6 remains separate from v7.

## Actions

- Posted hash, score, fixed-structure, and missing-ablation findings to
  `odkrywca_axioms` and `odkrywca_life` via `shared/board.py`.
- Added a note to H005 clarifying that record 141 is a distinct centered variant
  without its own matched full ablation.
- No hypothesis was promoted or refuted: the evidence does not support that.

Next: ask the life author to ablate context partition independently and test
parameter/palette robustness; ask the axioms author for a matched full ablation
and a centering-only comparison under the same capacity constraint.
