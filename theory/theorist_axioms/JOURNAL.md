# Journal — theorist_axioms

## 2026-10-22 — Local covariance plasticity as structural memory

### Starting question
What minimal constraint follows from continuous learning under bounded resources? A finite-state learner cannot retain arbitrarily many mutually distinguishable histories exactly: once histories exceed states, two collide, and any future query that separates them cannot be answered exactly for both. This is a pigeonhole argument, not a claim that useful lifelong learning is impossible. It suggests replacing “retain everything” with compression plus measurable forgetting/error.

### Candidate mechanism and definitions
Tested a local edge weight updated by source/target coincidence minus product of their running exponential traces, with nonnegative clipping and linear decay. An edge is considered structurally present when its weight exceeds a readout threshold. Full equations and caveats are in `THEORY.md`.

### Test run
Executed `nice -n 15 .venv/bin/python -I theory/theorist_axioms/sim/local_plasticity.py` on CPU. The deterministic stream has eight binary targets, with the source-correlated target changing from index 0 to 1 at step 6,000; other target events are chance-level. The code writes `sim/local_plasticity_result.json`; all reported numbers are from that execution.

At threshold .1, post-switch target occupancy after 100 steps was 1.0, but active-edge precision was .4023 before and .3545 after switch. Tightening the threshold to .5 gave occupancy .9761 and precision 1.0 before / .5881 after. Raising threshold reduces false positives in the first regime but does not eliminate stale/noisy edges in the second. No multi-seed or statistical claim is warranted.

### Conclusion / falsification status
The strong H1 expectation that local trace covariance plus decay alone both follows a new correlation and prunes unrelated edges is not supported; persistent false edges are a failure of the simple formulation. Rapid activation after switch is a narrow observation, not validation. Do not send to novelty auditor or experiment engine yet; the current variant is not a robust surviving idea. A distinct next hypothesis could add strictly local competition or resource normalization, but it needs a new, explicit test and control comparisons first.

### Limits
This toy setup uses a designed correlation signal and evaluates edge identity; it does not establish useful self-supervision, intrinsic goals, bounded-resource scaling, or Crafter competence. The exact covariance interpretation is approximate because the EMA traces update online.

### Coordination
Read the shared board before work; it contained a relevant note that Plan2Explore's Crafter score does not establish absence of backpropagation. Shared that this toy result is preliminary, not a Crafter candidate. Final board read performed before closing this iteration.

## 2026-10-22 — Probationary structural sprouting

### Why the prior experiment was insufficient
`budgeted_competition.py` gave high target coverage by keeping the globally top-scoring candidate edges. Its score updates are endpoint-local, but its active set is recomputed by ranking all `N` candidates at once; every candidate is effectively measured even before it exists as a contact. That does not demonstrate growth or pruning of a sparse structure. I kept it as a useful performance reference, not as a surviving structural mechanism.

### Mechanism and test
Added `sim/probationary_sprouting.py`. A source has a hard total contact budget, one slot reserved for a transient sprout, and a local neighborhood of possible partners. Uniform sprouting is the control. In the candidate rule, a new contact forms only when the source and an unconnected neighbor are coactive; one such neighbor is selected uniformly. The forming event is excluded from its covariance estimate to avoid counting a selection-conditioned observation. The contact is tested for 50 or 100 steps; a sufficiently correlated sprout stabilizes into a vacant mature slot or replaces a weaker mature contact. Existing contacts are pruned after 100 consecutive steps below a local score threshold. Updates use no target identity, reward, label, gradient, or full candidate ranking.

Ran with `nice -n 15 .venv/bin/python -I theory/theorist_axioms/sim/probationary_sprouting.py`. It completed on CPU and wrote `sim/probationary_sprouting_result.json`. The 20 deterministic seeds each had eight 1,500-step correlation regimes (`N=8`) and a matching null stream. For total capacity 2, coactive selection with 50-step probation yielded target coverage `.8806` (SD `.0316), 50-step sustained recovery in `179.1` steps on average and in all 160 regime windows, and stable-edge precision `.9053`. The max observed contact count was 2. The 20 null runs produced zero accepted births and zero stable edges.

### Ablations and interpretation
Uniform selection with the same capacity and probation reached `.7658` coverage, with `338.6` mean recovery steps and `.00153` null stable-edge occupancy. Coactive selection with 100-step probation fell to `.7189` coverage and `414.6` recovery steps. Capacity 3 reached `.8886` coverage and `167.1` recovery steps but precision fell to `.8110`. Therefore coactivity-gated growth plus a short evidence window is the useful combination in this controlled case; neither longer probation nor extra capacity was a free improvement. Fixed one-edge wiring has `.125` coverage under the balanced target schedule.

### Status / next falsifiers
This supports only the narrow H2 prediction recorded in `THEORY.md`; it is a candidate for `hyp.py`, not an established discovery. A replication with more seeds, different event rates, longer regimes, and larger `N` could refute it. The neutral `.5` trace prior and the assumption that an axonal growth site can sample coactive local neighbors are exposed assumptions. Next, test how blind coactive sampling scales with neighborhood size and whether local rate adaptation preserves null rejection under event-rate shifts before claiming robustness.

## 2026-10-22 — One codelength principle for structural change

### Direction change
The owner asked for one underlying law that yields learning, growth, pruning, memory, and exploration, rather than another collection of thresholds. H001 is therefore retained as a supported component result, but not as the target theory. Its fixed probation interval, growth/prune thresholds, reserved slot, and independent competition rule are exactly the controls to be replaced.

### Candidate principle
I defined a learner as a causal code for its own sensory stream. The single quantity is joint code length of sensory outcomes and the local architecture trajectory, under a physical state-size bound. Parameter updates are integrated Beta-Bernoulli codes; graph size is coded with the normalized universal prior `p(k)=1/[(k+1)(k+2)]`; local topology edits use that same prior conditioned on changing state; and segment lifetimes use the normalized, scale-free `p(d)=1/[d(d+1)]`. The posterior over graph paths is proportional to `2^(-L_total)`. The update rule is therefore posterior inference over a single codelength, without a separate growth threshold, pruning threshold, probe window, learning rate, or exploration bonus.

The derivation is in `THEORY.md`. For a fixed predictor q, expected data code length is `H(p)+D_KL(p||q)`. For two graph states, posterior log odds equal local predictive bits saved minus the difference in their structure/edit code lengths. This makes every topology change accountable to the same resource unit as prediction. The derivation does not prove that a local search can find the best code or that a finite posterior tracks a changing world.

### First reference test
Added and ran `sim/causal_code_filter.py` with `nice -n 15 .venv/bin/python -I`. It used 20 deterministic seeds, four 300-step regimes, `N=4`, a single local edge slot, one target channel exactly correlated with a source per regime, independent chance-level other targets, and a separate null stream. The current architecture at every prefix is the posterior mode under the code-path model; the prediction code itself is Bayesian and causal.

On target streams, mode edge coverage was `.9685` (SD `.0033), posterior mass on the current target edge `.9529`, mean delay to 25 consecutive correct-edge steps `10.16`, and success occurred in every regime window. The mode changed structure `9.8` times per 1,200-step run and occupied one edge on `.9766` of steps. Its mean prequential code length was `3.1196` bits/step. Fixed random one-edge wiring has `.25` coverage. On null streams, posterior mean edge mass was `.1841` but mode edge occupancy only `.00758` (SD `.0128); code length was `4.0227` bits/step. The finite state space guarantees no more than one edge.

### What the run does not establish
This is a reference Bayesian filter, not a finite-resource organism. It retains prefix evidence for all possible segment starts, evaluates histories for every candidate link even while absent, and the reported graph is a posterior mode rather than a coherent sampled trajectory. The seed-0–19 run is development evidence only; the registered seed-20–39 replication later refuted H002 on null MAP-edge occupancy. The posterior exposes uncertainty over alternatives but did not establish useful structural exploration, bounded memory, or return memory.

## 2026-10-22 — Confirmatory falsification and particle degeneracy

### Registered exact-filter test
The critic marked H002 `critiqued`; the experimenter then ran an independent exact code-path implementation on the registered fresh seeds 20–39. Target prediction passed: coverage `.96929 ± .00392`, mean recovery `9.8875 ± 1.2888` steps, and code length `3.11853` bits/step. Null code length passed at `4.02307`, but null MAP edge occupancy was `.04917 ± .16124`, above the registered `<.02` bound; seed 38 had occupancy `.72`. Posterior edge mass on null averaged `.21270 ± .12601`. Since every registered bound was required, H002 is refuted. Artifact: `experiments/h002-reference-replication/result.json`; status/history is in `shared/hyp.py show H002`.

The false edge is not just a particle-filter bug: the exact reference and bounded-population variants all fail on null seed 38. On that independently generated null stream, full-run centered source/output covariances were `[-.0025, -.0029, -.0262, -.0058]`; the largest absolute covariance over non-overlapping windows was `.1875` at 16 steps and `.04` at 300 steps. This is a diagnostic of the realized stream, not a significance test. It is consistent with the duration prior assigning enough mass to short regimes that accidental local dependence can buy its graph/edit code.

### Fixed-population approximation tests
After fixing an index-replacement bug, `sim/causal_code_particles.py` ran 128-particle prior-proposal SMC on the same seeds. Target coverage was `.95479 ± .00766`, recovery `14.45 ± 2.46` steps, and code length `3.14391`; null MAP edge occupancy was `.30004 ± .40410` and posterior edge mass `.36714 ± .36868`. Eight of twenty null seeds spent more than `.05` of the run on a false edge. This first approximation had severe particle impoverishment.

`sim/causal_code_particles_move.py` added a Gibbs update of the current segment architecture, conditional on its integrated data code and the transition prior. It still had null MAP occupancy `.20738 ± .36280`; five seeds retained a false edge for substantial portions of the run. The conditional transition model prevents a segment's state from being Gibbs-resampled to the preceding state unless the two segments are merged, but the particle did not retain the previous segment data needed for that merge. This is an implementation limitation, not evidence for a new learning mechanism.

`sim/causal_code_particles_self_segments.py` tested a distinct path prior: each segment independently pays its graph code, so self-transitions are allowed and predictor statistics reset at segment boundaries. Target coverage was `.95008 ± .00728`, recovery `15.475 ± 2.253`, and code length `3.14414`; null MAP occupancy fell to `.03375 ± .12702`, but seed 38 still occupied a false edge `.585` of the run. Max retained particle-state object size was 248,373 bytes for 128 particles. The particle state uses fixed-width floating counters, but the simulation harness retains the generated stream and diagnostic traces; this is not yet an end-to-end bounded-memory candidate. These runs improve an approximation, but do not rescue H002's registered prediction or demonstrate return memory.

### Interpretation / next question
The null failure on the same seed in the exact and approximate filters points to path-model flexibility, not just resampling. A data code plus a graph prior and a hand-selected duration prior is still a family of choices; its posterior can rationally encode short accidental correlations. The independent-segment prior reduces, but does not eliminate, this false structure. H002 has no persistent parameter state for a dormant/removed edge, so it cannot claim fast memory on a returning regime. The next useful test should make recurrence explicit and measure first acquisition versus return; the next theory should account for storage and reuse of predictive structure in one resource-coded state, without adding a separate memory mechanism. No successor hypothesis is registered until a mechanism survives that test.

### Return-memory diagnostic
Ran `sim/causal_code_return_test.py` on the exact reference code path with `N=2`, 20 seeds 20–39, and three 300-step regimes in the sequence A–B–A. The filter followed the stream well overall (target coverage `.98144 ± .00413`; all regime windows reached the 25-step sustained criterion). For the repeated A edge, initial recovery averaged `5.75` steps and return recovery averaged `6.05`; paired return-minus-first delay was `+0.30` steps (across-seed SD `2.55`, 3/20 ties). This is no measurable return advantage. The test matches the implementation: segment predictor statistics are reset at each graph change and the prior does not give a previously seen graph a cheaper reference code. Artifact: `sim/causal_code_return_test_result.json`. It is a diagnostic, not a general memory theorem; the physical one-edge cap and exact-history cost remain.

## 2026-10-22 — Persistent local evidence under A–B–A

### Question and mechanism
Tested whether retaining local predictive evidence across structural switches is enough to turn recurrence into memory. `sim/return_trace.py` generated 40 deterministic four-channel A–B–A streams. A target channel carried a noisy copy of a binary source in A (channel 0) and B (channel 1), with 8% flips and 500 steps per regime. Each channel stored an unbounded signed coincidence sum; the selected architecture was its current argmax. A reset-evidence control cleared those sums at each regime boundary.

### Run and result
Ran `nice -n 15 .venv/bin/python -I theory/theorist_axioms/sim/return_trace.py`; output is `sim/return_trace_result.json`. Persistent-evidence first acquisition was 1.15 steps on average, but return-to-A took 29.325 steps; paired return-minus-first was +28.175 steps and only 5% of seeds returned faster. The reset control was 1.15 steps initially and 1.275 on return. During returned A, the persistent winner was channel 0 for .9418 of steps, but that eventual occupancy conceals the slower reacquisition.

### Conclusion
Falsified the naive principle “memory is retained local evidence” as a useful A–B–A memory rule. An unbounded association score stores both regimes without context, so B's accumulated evidence initially suppresses the returning A. This isolates a requirement: stored predictive evidence must be retrievable by context, or active evidence must be separable from dormant memory. That is a new hypothesis, not yet a result. Do not submit a candidate; continue only with explicit return latency and capacity tests.
