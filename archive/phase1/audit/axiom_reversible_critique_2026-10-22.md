# Audit: `axiom_reversible`

Scope: `candidates/axiom_reversible/principle.py`, H006, and leaderboard entries 32--33.

## Verdict

The 51.5987 Snake score is an evaluator-specific controller artifact, not evidence for H006. The candidate is disqualified and must not be treated as a supported GENESIS result.

## Reproduction and evidence

- `System.__init__` hard-codes a 10x10 Hamiltonian traversal in `path` (lines 5--10). The Snake board dimensions and the route are known before any observation.
- `step` only sets `length = 1 + sum(obs[400:500])` and returns `[0.5] * len(obs)` (lines 13--15). It never learns or predicts the next sensory observation.
- `act` reads the head position/direction/body from the observation (lines 17--22), looks up the next hard-coded route cell, and emits the corresponding action. This is direct board-state control, not a reversible learner.
- `structure()` reports `units=connections=length`, where `length` is derived from the body plane in the current observation (lines 24--25). Thus the structural mass is evaluator-visible state copied from the board, not an internal learned structure.

The nominal level-3 record (leaderboard entry 33) reports survival `1000/1000` for all seeds, apples `28,19,20`, board coverage `1.0`, and structure Spearman `0.9997`, but `unique_action_triplets=13` and `structure_direction_fraction=0.0`. The level-3 score is 51.5987 versus the 35.3814 gate. The same code under parameter perturbation (`n=10`) scored only 12.0992 with robustness 0.2305 (entry 32), showing that the apparent pass depends on the unparameterized hard-coded route.

The stream interface is also untested by the pass: `step` is a constant predictor, and the entry was run with `--only-level 3`. The registered H006 falsifier explicitly excludes a fixed hidden route and requires learning/return under perturbation; this implementation violates those requirements directly.

## Action

H006 should be marked refuted for the submitted implementation. Any future test must remove the hard-coded board route, use a fresh unseen task/layout, require online change in predictions/actions, and report a meaningful internal structure independent of evaluator observations.
