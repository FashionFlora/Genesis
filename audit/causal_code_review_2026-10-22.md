# Review of the minimum causal description-length candidate

Scope: the “Unification pivot — minimum causal description length” in theory/theorist_axioms/THEORY.md and its reference implementation theory/theorist_axioms/sim/causal_code_filter.py. It was not registered in hyp.py at review time. This review separates prior art, mathematical consistency, implementation, and empirical evidence.

## Prior-art verdict: partial overlap with a known framework

The central principle is established: select predictive structures by sequential data code length plus a structure/path code. Bornschein, Chiappa, Malek, and Ke (2021), “Prequential MDL for Causal Structure Learning with Neural Networks,” arXiv:2107.05481, explicitly use a prequential predictive score to rank Bayesian-network structures and obtain complexity regularization from MDL. The paper’s CPDs are neural networks and its implementation trains them with gradient-based optimization; this differs from the candidate's exact Beta-Bernoulli integrated code and stated no-gradient implementation. The paper nonetheless directly establishes that “choose a causal graph by how compactly it codes sequential predictions” is not itself a new principle.

Adams and MacKay (2007), “Bayesian Online Changepoint Detection,” arXiv:0710.3742, derive online posterior filtering over run length, with predictive probabilities, sufficient statistics, and a prior/hazard over segment duration. The candidate adds a graph state and edit prior to this known online Bayesian segmentation pattern. Its p(d)=1/[d(d+1)] is a particular scale-free duration prior, not a derivation that eliminates prior choice.

I found no exact identity between the inspected sources and this specific combination of a finite local edge-state space, Jeffreys Beta-Bernoulli segment codes, the current graph-size prior conditioned on capacity, topology transitions conditioned on a change, and the stated duration prior. This bounded search supports a partial-overlap verdict, not an exact-priority claim. The high-level mechanism is MDL/Bayesian model selection with online changepoint inference. It is not an explicit FEP, maximum-entropy, or empowerment objective; posterior uncertainty alone is also not action exploration.

## Does one principle derive the claimed behaviors?

For the stated reference problem, the code-length posterior can select a different edge after the data become better explained by that edge. Integrating Beta-Bernoulli parameters supplies online predictor adaptation, and path persistence represents a finite-horizon structural trace. Those are coherent consequences of this specified Bayesian model.

The implementation does not yet demonstrate the whole claimed principle:

- The architecture state space is fixed to no edge or one of four candidate edges (N=4, capacity one). There is no neuron birth, no new endpoint generation, and no way to represent structures outside this list. The cap is imposed by the state space.
- Jeffreys Beta(1/2,1/2), graph-size prior p(k)=1/[(k+1)(k+2)] conditioned on k≤1, uniform edge identity given k, transition probabilities conditioned on a topology change, and p(d)=1/[d(d+1)] are explicit prior choices in the current source. They replace thresholds and learning-rate constants with coding/model choices; they do not remove design choices.
- The dynamic program enumerates every candidate architecture and every possible segment start in its one neighborhood. This is not network-wide sorting, but neither is it an independent endpoint-local update. The filter stores O(T*N) prefix counts and O(T^2*N) segment costs, so its memory is unbounded in stream length. The graph is not the sole memory state.
- The implementation records posterior mass and the maximum-a-posteriori state. It does not sample a coherent architecture path. Therefore “exploration is a posterior draw” is a proposed interpretation, not behavior tested by this code.
- The test concerns structural alternatives for next-observation prediction. It has no action choices, so it does not test behavioral exploration or empowerment.

The algebraic statement that a normalized prequential predictor has expected code length H_p(Z_1:T)+D_KL(p||q) is correct when the expectation is under a specified true joint distribution p and q is a normalized joint predictor. For the general formula in THEORY.md, define the factorization assumptions explicitly: a product of same-time local conditionals is a normalized joint only under an acyclic graph (or another explicitly normalized construction). Otherwise its negative log score need not be a code length. The current toy code avoids this ambiguity by scoring a source and target conditionally in a fixed order.

“Causal” also overstates what this experiment identifies. The learner sees observational source-target co-occurrence and selects a useful predictive parent. There are no interventions, counterfactual tests, or stated identifiability assumptions that distinguish direct causation from a common cause. The simulator constructs the target by copying the source, but that generator fact is not available to the learner. Call the current result predictive edge selection unless a causal-identification claim and a discriminating test are supplied.

## What the recorded run establishes

The result file reports 20 seeds, four 300-step regimes, N=4, one-edge capacity, and a target that copies the source in a different channel each regime. It reports mean MAP target coverage 0.9873 (SD 0.0040), mean recovery delay 4.075 steps (SD 1.356), target-stream prequential code 3.1162 bits/step (SD 0.0033), and null MAP edge occupancy 0.1000 (SD 0.0669). Mean null posterior edge mass is 0.4009 (SD 0.0542), much less decisive than the MAP occupancy alone suggests. These values are from theory/theorist_axioms/sim/causal_code_filter_result.json.

The first result artifact was stale relative to the source: it recorded a uniform initial/edit prior after the source had changed to the graph-size prior. The author regenerated the result at 12:55 with parameters matching the updated source. That mismatch is resolved. However, H002 was registered later with a confirmatory prediction on fresh seeds 20–39, while the regenerated result still uses seeds 0–19. Those values are development evidence and do not test the registered fresh-seed prediction.

## H002 registered proposal follow-up

H002 is now registered with the narrow prediction and explicit falsifier. The current 20-seed development result meets its numerical bounds: MAP coverage 0.9685, mean recovery 10.16 steps, null MAP occupancy 0.00758, target code 3.1196 bits/step, null code 4.0227 bits/step, and a hard one-edge state space. The proposed fresh-seed test on seeds 20–39 remains outstanding.

The audit findings still apply to that test. Current code evaluates all four absent-edge alternatives retrospectively from the observed source/target stream and retains all possible segment starts; this is a centralized exact model comparison for one small neighborhood, not local growth from an existing sparse graph. The mode trajectory changes its reported topology, but there is no sampled physical graph path or bounded-memory implementation. The state cap makes the one-edge bound true by construction.

For the general THEORY.md objective, require a normalized joint predictor before calling its negative log a code. Same-time local conditionals form a normalized joint under a DAG/factorization order (or an explicitly normalized alternative); arbitrary directed local graphs, including cycles, are not enough. The current source-to-target toy code has a fixed valid order and avoids this particular issue. The observational experiment still supports predictive edge selection, not causal identification.

H002 is therefore **critiqued**: prequential MDL and Bayesian changepoint inference are known principle families, while this exact combination remains a specific testable construction. Its current predictive test is pending on the registered fresh seed set, and its unifier claims about bounded memory, actual exploration, and neuron growth remain untested.

The generator's regime identity is used in result scoring, not in the architecture update; the update loop gets observations and the selected candidate state. There is no external reward, target label input, or gradient. Thus I found no reward/label/gradient leakage in the implemented filter. The data are nevertheless deliberately easy: balanced Bernoulli source, exact copying in one target, independent Bernoulli distractors, and deterministic equal-length regime changes. The result has 20 seeds but no matched fixed-edge, no-edge, fixed-duration, or alternative-prior comparison in its report. It does not establish that the codelength rule is necessary, that its duration prior helps, or that it beats a simple online change detector.

## Required next step before registering a strong unifier claim

Register a falsifiable hypothesis with an exact scope. Compare against a no-edge predictor, a fixed edge, a matched-capacity fixed-topology/online learner, and an online changepoint baseline under the same stream, seeds, and compute. Include ablations for the edit code and duration prior. Use nonperiodic regime lengths and a matched nonstationary null. Report prequential bits and Brier/log loss, edge precision/recall, recovery, null occupancy and posterior calibration, plus memory versus T. If posterior sampling is the exploration claim, implement and evaluate sampled graph trajectories separately from MAP decoding.

To test the “single principle” target, show that a bounded-memory approximation preserves the posterior predictions while actually limiting persistent state; then specify how candidate neurons/endpoints arise. Until then, the precise result is a successful reference calculation for one fixed finite architecture space, not a bounded self-building learner.

## Opened sources

- Bornschein, J., Chiappa, S., Malek, A., and Ke, R. N. (2021). “Prequential MDL for Causal Structure Learning with Neural Networks.” Full text opened through shared/lit.py: https://arxiv.org/html/2107.05481
- Adams, R. P. and MacKay, D. J. C. (2007). “Bayesian Online Changepoint Detection.” Full text opened through shared/lit.py: https://arxiv.org/html/0710.3742

Search scope: focused shared/lit.py arXiv/web searches for prequential MDL, causal structure learning, and online Bayesian changepoint detection, plus the local audit registry. Search date: 2026-10-22. No claim of exhaustive search.

## H002 registered-seed result and particle-variant follow-up

The independent exact-filter test on registered seeds 20–39 is now recorded in `shared/hyp.py` and `experiments/h002-reference-replication/result.json`. It passes target coverage (`0.9693 ± 0.0039`), recovery (`9.89 ± 1.29` steps), target code (`3.1185 ± 0.0040` bits/step), null code (`4.0231 ± 0.0016` bits/step), and the one-edge state constraint. It fails the registered null MAP edge occupancy bound: `0.0492 ± 0.1612` versus `<0.02`, with seed 38 at `0.72`. The falsifier says failure of any registered bound refutes the prediction, so H002 is correctly `refuted`. The result concerns the exact reference filter; it does not validate or refute an approximation's behavior independently.

I also inspected the new, not-yet-executed `sim/causal_code_particles_move.py`. It uses a 128-particle posterior approximation, resamples particles every observation, Gibbs-resamples the current segment's architecture under the explicit transition prior and integrated code, and resets sufficient statistics on topology transitions. Its output artifact `causal_code_particles_move_result.json` was absent at review time. This code has no obvious target-label or reward leakage: the target index is used for scoring posterior mass and coverage, not in the predictive or particle-update functions. It does, however, remain a finite Bayesian/MDL model-selection construction, closely related to the already reviewed prequential-MDL and Bayesian online changepoint families. Its architecture is still restricted to no edge or one of four pre-enumerated edges; the `128` particles are a fixed approximation budget, and all candidate-edge sufficient statistics are retained in every particle. Structural “exploration” is uncertainty over this finite model set, not action exploration or creation of new neuron types. Segment statistics reset on edits, so persistent return-memory is not established. The saved null/target metrics must distinguish the weighted posterior mode from the post-resampling particle-population mode; particle diversity/ESS should also be reported because resampling occurs at every step.

Do not use this unexecuted particle variant to reopen H002's verdict. If it becomes a new candidate, register its bounded prediction and falsifier before reading a confirmatory result, compare it with the exact reference on the same seed family, and report both posterior-mode and sampled-structure metrics. The broader mechanism's prior-art and “one law” limitations above continue to apply.

## Executed particle variants

Both particle result artifacts have since appeared. `causal_code_particles_move.py` on the same registered seeds 20–39 reaches target MAP coverage `0.96125 ± 0.00860`, recovery `12.86 ± 2.48` steps, target code `3.14074 ± 0.01544` bits/step, and null code `4.02531 ± 0.00341`. It still fails the registered null MAP occupancy limit: `0.20738 ± 0.36280`, with seed 38 at `0.95833`.

`causal_code_particles_self_segments.py` allows adjacent segments to keep the same graph while resetting predictor counts. It reaches target coverage `0.95008 ± 0.00728`, recovery `15.475 ± 2.253` steps, target code `3.14414 ± 0.01894`, and null code `4.02465 ± 0.00473`. Null MAP occupancy is `0.03375 ± 0.12702`, still above `<0.02`; seed 38 is `0.585`. This self-transition is a parameter-reset event with no graph change, so its reported structural-change count does not expose every state reset. The saved artifact reports particle payload size about 248 KB for 128 particles, but the run materializes the full generated stream and diagnostic traces; it is not an end-to-end streaming memory test. Neither variant records particle ESS/diversity despite resampling every step.

Both variants use the same registered seed range and still fail the null bound, so they do not rescue H002. Their changed transition rules and Monte Carlo approximation are development branches of the already refuted code-posterior idea, not new registered hypotheses. Target labels are used for evaluation only in these implementations, as in the exact filter. H002 remains `refuted`.
