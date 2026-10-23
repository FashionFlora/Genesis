# H003 independent stage-1 stream audit

Scope: `theory/theorist_life/stream_agent.py` and `theory/theorist_life/stream-stage1/result.json`. This is an audit of the independent benchmark implementation, not a replacement for H003's registered paired test in `sim/resource_flux_ecology.py`.

## What this artifact establishes

The runner exposes the agent only to the current observation and the next sensory observation. Reward and regime metadata are evaluator-only; the current target channel is used only for scoring. I found no reward, regime-label, target-index, or gradient leakage in the interface or update path.

The run has five seeds, 6,000 steps per seed, and the hidden repeated schedule A/B/A/C/B/A with 1,000-step phases. H003's `ResourceFlowPredictor` has mean target MSE `0.18764`, compared with `0.11241` for `fixed_hebb` and `0.10531` for the reference `growing` agent. Its reported adaptation mean is `345.69` steps versus `66.12` and `89.76`; that mean excludes phase visits that never crossed the target-MSE threshold, so it is a success-conditional summary. Return-forgetting MSE is `0.18004` for H003, between the two baselines (`0.12234` and `0.23499`). These are five-seed descriptive means; the artifact does not report uncertainty intervals.

This is not a direct test of H003's registered prediction or falsifier. It has neither the cell-specific versus neutral same-total-cost control nor the higher-mutation neutral control, and the agent does not report source-edge counts, so active-edge share is missing. Its stream schedule and implementation also differ from H003's registered three-edge ecology. The poorer MSE against both structural baselines is a meaningful benchmark warning, but it does not by itself refute the registered paired selection effect.

## Single-principle audit

The tested implementation does not derive learning, memory, mutation, and structural change from one rule:

- Each cell updates explicit Beta-Bernoulli counts with unit pseudocounts. Resource flow does not determine this update.
- Daughter cells copy those counts and their edge; a mutated daughter resets its counts. This is an explicit memory-inheritance rule.
- Mutation uses a fixed probability `0.05` and uniform sampling from the other source-target pairs. Neither the rate nor the proposal distribution follows from mass flow.
- Death is coded as `mass <= 0`; fission is coded as `mass >= 2`. The resource state determines whether these events occur, but the event rules and mass scale are supplied separately.
- Initialization creates one cell for each of the 64 possible input-output pairs. Thus the starting architecture is already complete for this finite bipartite candidate set. Cell births can duplicate edges and mutation can change an instance's endpoints, but the experiment does not show growth from a sparse graph or discovery of endpoints outside the enumerated set.

In the five recorded runs, about 20,255–20,638 fissions and 20,241–20,638 deaths occur per 6,000 steps, while final cell counts remain 53–78 around the initial 64. Only 9–13 distinct edge types remain at the end. This is high population turnover around a roughly stable population, not evidence that 20,000 distinct structural innovations accumulated. The substrate inflow is also calibrated from a presumed baseline error of `0.25`; the implementation supplies maintenance `0.10`, error cost `0.25`, and the mutation rate as fixed constants.

The mechanism is best described as prediction-error-mediated differential persistence and reproduction, a known selection principle family already reviewed in `audit/resource_flux_review_2026-10-22.md`. The independent stream test shows that the current implementation transfers poorly to this benchmark relative to its structural baselines; it does not demonstrate a new common law or a successful self-building predictor.

## Discriminating next test

For an independent test of H003, keep its registered target/neutral conditions and seed pairing, but start from a sparse graph that lacks the next predictive edge. Report active-edge share from the evaluator and from the agent's structural state separately, target MSE, all regime visits including threshold failures, per-seed paired intervals, population/mass accounting, and distinct edge types. To test the unifier claim, ablate or derive the Beta update and mutation proposal rather than treating them as consequences of resource flow; retain the current benchmark baselines and include mutation-off and same-rate neutral arms.
