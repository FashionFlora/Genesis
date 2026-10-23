# Journal — theorist_axioms

## 2026-10-23 — Axiomatic action identifiability limit

Completed the third and final turn on the action-identifiability direction.
Re-ran `nice -n 15 .venv/bin/python -I
theory/theorist_axioms/sim/action_identifiability.py`. The 40 paired worlds
had identical passive histories and mean difference `0.0`; their best actions
were opposite in all 40 pairs. Result: `sim/action_identifiability_result.json`.

This is a no-go result for passive derivation, not a failed parameter setting:
identical observation laws give a passive-history policy the same action
distribution in both worlds. A self-building action principle therefore needs
intervention-conditioned evidence and an endogenous ordering of consequences;
neither is supplied by prediction or memory. The direction made no progress
toward an identifiable action rule within its three-turn budget and is parked.
No candidate or judge run is warranted. The proof and measured witness are
recorded in `THEORY.md`.

## 2026-10-23 — Re-run of the action derivation test

Ran `nice -n 15 .venv/bin/python -I
theory/theorist_axioms/sim/action_identifiability.py` again for the requested
maturity test. Across 40 pairs and 1,000 passive observations per world,
`passive_pairs_equal=true`, mean passive difference was `0.0`, and
`worlds_choose_opposite_actions=true`. The metric did not improve: no passive
predictor can distinguish which optimum applies in this pair family.

Conclusion: the same reversible-surprise exchange rule cannot derive an
action. It lacks action-conditioned evidence and a criterion that orders
consequences. An action rule based only on its passive state is compatible
with both optima, so adding one would encode an extra axiom. No `act()` or
candidate was added; no judge run was warranted. Next direction turn should
seek a derivation of both missing conditions from self-building constraints,
not from reward or task-specific resources. Result:
`sim/action_identifiability_result.json`.

## 2026-10-23 — Reversible memory does not derive action

Repeated the maturity test for `reversible_surprise` with
`nice -n 15 .venv/bin/python -I
theory/theorist_axioms/sim/action_identifiability.py`. Across 40 paired worlds
and 1,000 passive observations per world, every pair had identical passive
histories (mean difference `0.0`) and opposite optimal actions. The output is
in `sim/action_identifiability_result.json`.

The principle exchanges a predictive state after surprise, but has no
action-conditioned observation and no ordering over outcomes. Therefore its
state is compatible with opposite action optima, so adding an `act()` would
require another principle or an encoded preference. No action was added and no
candidate was sent to the judge. The missing axiom is an endogenous criterion
that orders counterfactual consequences while remaining identifiable from the
system's own experience; mere persistence of a predictive distinction is not
that criterion.

## 2026-10-23 — Context-addressed action evidence crossover

### Mutation and novelty check
Created `candidates/contextual_action_reversible_evidence/` from
`action_conditioned_predictive_sufficiency` and
`contextual_causal_intervention`. It maintains separate action-conditioned
outcome evidence by parity context, preserving those predictors for recurrent
contexts; `act()` samples the action with least accumulated outcome evidence.
The mechanism description passed `python3 shared/ideas.py check` as new
(maximum similarity `.08`).

### Paired action test
Ran `nice -n 15 .venv/bin/python -I
theory/theorist_axioms/sim/contextual_action_identifiability.py`. In 40 pairs,
passive observations were identical, but uncertainty-seeking selected the
same action allocation in both orientations; it failed to identify opposite
preferences in `40/40` pairs (`identified_opposite_optimum=false`). Artifact:
`sim/contextual_action_identifiability_result.json`. Thus context addressing
and causal evidence do not supply a value ordering; they support exploration,
not a preferred consequence.

### Judge and maturity result
Ran `nice -n 15 .venv/bin/python -I sandbox/judge.py
candidates/contextual_action_reversible_evidence --author odkrywca_axioms`.
L1 score `11.5897`, Brier `.25261`, robustness `.9996`, highest level `0`
(gate `26.2446`); learning gate passed but predictive skill versus `.5` was
zero. H030 is refuted for action identification and this candidate does not
transfer to the benchmark. The requested maturity question remains negative:
the exchange law of `reversible_surprise` contains neither action-conditioned
effects nor an outcome ordering, so its existing `act()` is not derivable.

## 2026-10-22 — Context capacity and recurrent return

H014's context address was swept without changing its mechanism. The causal-map
signature variant failed to transfer (`candidates/coactivity_context_signature`,
L1 `49.0625`), so it is not retained as the main candidate. Bit-context
coactivity with `timescale=8, contexts=8` is saved as
`candidates/coactivity_context_blend9/principle.py`.

The full judge passed levels 1 and 2: L1 `50.4087`, Brier `.18698`, robustness
`.9949`; L2 `30.8583`, Brier `.23172`, robustness `.9862`. Learning gates passed
on both levels. The L2 score is below the earlier H014 variant (`31.0923`), so
this is not a leaderboard improvement. The level-3 stop is the expected missing
`System.act` interface.

The independent A-B-A diagnostic is
`sim/context_signature_return_result.json`: first-A MSE `.25633`, return-A MSE
`.24580`, B MSE `.25367`, and return-minus-first `-.01054` across 12 seeds.
This is a small return benefit, while the context channel is an explicit probe;
it supports continued testing but does not establish general memory.

## 2026-10-22 — Causal-gated plasticity and return memory

### Direction
H002 and address-indexed persistent traces did not show a faster A-B-A return.
The successor principle tested here is that prediction error gates exploration:
only the currently active causal address receives persistent plasticity, while
dormant predictive addresses are conserved. A sustained error opens a local
search over alternatives. Memory is therefore protected causal structure, not a
pooled trace.

### Test
Ran `nice -n 15 .venv/bin/python -I theory/theorist_axioms/sim/causal_gating.py`.
The 40-seed, four-channel A-B-A stream starts from an unrelated address so
first acquisition measures discovery. First acquisition was `27.625` steps;
return A was `0` steps; return was faster in `40/40` seeds and paired
return-minus-first was `-27.625`. Mean Brier was `.17649`. On the independent
null stream Brier was `.25633` and return-address occupancy was `.2703`.
Artifact: `sim/causal_gating_result.json`.

### Candidate check
Saved `candidates/causal_gated_plasticity/principle.py` and ran the level-1
judge. It passed the learning gate but scored `4.1982` with mean Brier
`.25484`, robustness `.908`, and AST penalty `.74`; it is far below the
`26.2446` level-1 gate and is not a leaderboard contender. The mechanism
survived its registered toy falsifier, but the candidate implementation did
not transfer predictive quality to the judge world.

### Status and next test
Registered as H012 (`testing`). The main metric improved versus addressability
(`+1.175` return-minus-first to `-27.625`), while judge score did not improve.
Next test: simplify the candidate and add a bounded exploratory shadow trace;
park after the stated three-turn budget if judge Brier/score does not improve.

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

## 2026-10-22 — Causal addressability test

### Principle
Persistent predictive state must be indexed by a distinguishable causal address (here, target channel plus local rule), while a short active trace selects the address currently explaining the stream. A shared rule library can seed an unseen address; it must not pool evidence from different addresses. Growth/pruning are not claimed by this diagnostic.

### Execution
Added `sim/causal_addressability.py` and ran `nice -n 15 .venv/bin/python -I theory/theorist_axioms/sim/causal_addressability.py`. Forty seeds use five 400-step phases with target schedule `0,1,3,2,0`, noisy copy relation (flip `.08`), four channels, and no regime metadata. The addressed model stores per-(channel,rule) Beta counts plus a short activation trace; the independent control removes the shared rule prior; the pooled control uses one signed score per address.

### Recorded result
Artifact: `sim/causal_addressability_result.json`. Addressed mean MSE `.21019`; target MSE by phase `.08914,.08195,.08291,.08240,.08490`. First A recovery `11.00` steps, return A `12.18`, and held-out channel 2 `10.05`. Independent control: held-out channel `220.98`, return A `184.88`; pooled control: MSE `.25`, return A `50.35`. Null addressed MSE `.25016`, near chance.

### Interpretation and limit
Address-indexed dormant state prevents the interference seen in `return_trace.py` and reuses a learned copy law at a new channel. The return is not faster than first acquisition, so this is evidence of retained usable state, not a strong consolidation theorem. The test has a fixed four-address library and no structural birth/death; no `candidates/` entry or board post is justified. Next: vary rule identity (copy/invert), address capacity, and add a stream-level structural birth/death test.
 
## 2026-10-22 — Error-gated shadow alternatives

H012 was tested as a compact candidate: all causal addresses receive a bounded
decayed shadow trace, but an address switch occurs only after sustained local
prediction error. Candidate: `candidates/error_gated_support/principle.py`.

After correcting the temporal alignment, 40 seeds gave return-minus-first error
`+0.000119`, faster return in `.55` of seeds, and null MSE `.25653`. Artifact:
`sim/error_gated_support_result.json`. H012 is refuted.

Judge level 1 was `24.1318` (Brier `.19249`, robustness `.9472`, AST multiplier
`.4845`), below the `26.2446` gate. A dual fast/slow dormant trace improved its
return-memory component to `.0453` but worsened Brier to `.19524` and scored
`20.7621`; this direction is parked rather than tuned.

## 2026-10-22 — Reversible surprise switching

### Principle and test
The next candidate treats memory as a reversible state exchange. Each local
source-target relation has an active conditional predictor and a dormant
predecessor. When the previous prediction is surprised, the two relation states
are exchanged; the active state learns the new transition while the predecessor
remains intact. This uses no phase bit, reward, backpropagation, or pooled
long-term score. Candidate: `candidates/reversible_surprise/principle.py`.

Ran `nice -n 15 .venv/bin/python -I theory/theorist_axioms/sim/reversible_surprise_return.py`
on 40 seeds and 500-step A-B-A phases. First error was `.2367462`, return error
`.2131532`, and return-minus-first `-.0235930`; return was faster in `.625` of
seeds. Null mean error was `.2264123`. The return metric improved by `.00243`
against the prior no-context total-evidence test (`-.0211595`).

The judge passed levels 1 and 2 with score `22.3923` and robustness `.8607`
(level 1 score `29.6224`, level 2 `22.3923`); it is far below the leaderboard
and lacks `act` for level 3. H017 remains `testing`: the diagnostic supports
reversible retention, but transfer quality is poor and one-step surprise may
be too sensitive to noise.

### Exchange-count diagnostic

Instrumented the same candidate without changing its transition rule in
`sim/reversible_switch_count.py`. On 40 seeds and three 500-step phases, the
candidate exchanged an average of 21,226.8 source-target states per A-B-A run
and 21,459.5 per independent null run (about 14 exchanges per step in either
case). Artifact: `sim/reversible_switch_count_result.json`. Thus raw surprise
does not distinguish a causal regime change from null prediction noise; this
does not measure a new memory improvement. Next test: exchange an individual
relation only when its dormant conditional predictor has lower error than its
active predictor in the observed source context.

## 2026-10-22 — Predictive bank recall crossover

### Hypothesis and test
H025 crossed `reversible_surprise` with fit-based retrieval: two retained local
predictors compete per target using only their previously accumulated
prequential error, and only the selected bank receives the current transition.
The diagnostic uses 40 seeds, 500-step A-B-A phases, four output channels, a
lagged source-to-output relation, and an independent Bernoulli null. The first
prototype incorrectly selected with the current target; that leaked information
and was discarded. Audit also found the inherited stream confused the source
with target A and used a contemporaneous, not lagged, relation. The retained
result uses selection-before-observation and a corrected lagged stream.

### Result
`nice -n 15 .venv/bin/python -I theory/theorist_axioms/sim/predictive_bank_recall.py`
gave first-A error `.0883664`, return-A error `.1228077`, return-minus-first
`+.0344413`, and faster return in `.15` of seeds. The original rule on the same
corrected stream gave `.3177003`, `.2934721`, `-.0242282`, and `.55`; null mean
error for the new rule was `.2757845`. The effect fails the registered recall
prediction. Result file: `sim/predictive_bank_recall_result.json`.

Saved the required crossover as `candidates/predictive_bank_recall/` and ran
`nice -n 15 .venv/bin/python -I sandbox/judge.py candidates/predictive_bank_recall`.
L1 score was `16.1539` versus required `26.2446`, robustness `.7917`, highest
passed level `0`; the candidate is below baseline and long-track eligible.
H025 is `refuted` in `shared/hyp.py`.

### Action derivation check
This rule predicts sensory transitions and retains predictive states. It has no
estimate of outcomes under an unchosen action, so it cannot derive an action
selection rule without a causal intervention model. No `act` was added; adding
Snake geometry or reward-shaped internal variables would change the principle.

## 2026-10-22 — Context-action sufficiency and the action boundary

Re-ran `nice -n 15 .venv/bin/python -I theory/theorist_axioms/sim/action_conditioned_sufficiency.py`.
Across 40 seeds on the noisy `cue XOR action XOR context` A-B-A stream,
context-action indexed prediction reached MSE `.07771`, with first-A window
MSE `.15177` and return-A `.06981`. The context-free/action-free pooled model
had MSE `.25215`; the independent null context-action model had `.25654`.
Artifacts: `sim/action_conditioned_sufficiency_result.json` and
`sim/action_conditioned_sufficiency.py`. This supports retaining distinct
interventional outcomes under context and a returning context, within this toy
family; it does not show that an agent chooses useful actions.

Maturity check for H017: reversible surprise alone cannot imply `act`. A
passive conditional transition distribution is compatible with different
unobserved action-effect maps, so the preferred intervention is unidentified.
Even after adding an action-conditioned causal model, prediction alone supplies
no ordering over outcomes; exploration or preference needs another derivation.
No action heuristic or Snake candidate was added. H026 moves to `testing`.

Evaluated the existing `candidates/context_action_sufficiency/principle.py` with
`nice -n 15 .venv/bin/python -I sandbox/judge.py candidates/context_action_sufficiency`.
It scored L1 `14.9141` (required `26.2446`), robustness `.9999`, and passed no
level. The toy result therefore does not transfer to the benchmark stream. The
candidate's action-indexed predictor also has no observed latent-context
inference or outcome preference; keep H026 as a narrow memory hypothesis, not
as a demonstrated action principle.

## 2026-10-22 — Passive prediction does not identify action

For the requested maturity check on `reversible_surprise`, tested whether its
passive predictive state alone can identify an action. `sim/action_identifiability.py`
constructs paired worlds with identical passive streams and opposite
action-effect maps, across 40 seeds and 1,000 observations per seed. The run
reported identical passive pairs in 40/40 and opposite best actions in 40/40
(`sim/action_identifiability_result.json`). No `act` was added: the same
predictive state is consistent with opposite interventions, so choosing one
requires action-conditioned causal evidence plus a value ordering. The
reversible memory principle supplies neither. No new candidate was submitted.

## 2026-10-22 — Fit-selected predictive exchange crossover

Created `candidates/contextual_predictive_exchange/` as a crossover of
`context_action_sufficiency` and `reversible_surprise`. It keeps two local
Bernoulli predictors per source-target-action relation and routes an observed
outcome to the predictor with lower accumulated squared prequential error.
The description passed `python3 shared/ideas.py check` (maximum similarity
`.11`).

Ran `nice -n 15 .venv/bin/python -I sandbox/judge.py
candidates/contextual_predictive_exchange`. Level 1 score was `10.8456`,
robustness `.9997`, mean Brier `.25204`, and prediction skill versus constant
`.0`; it passed no level (baseline `20.9957`, gate `26.2446`). This benchmark
does not establish a return-memory benefit: no distinct dormant state was
shown to be acquired and retrieved. Treat this as a negative transfer result.
The candidate's nominal `act` explores by uncertainty; level 1 does not test it.

Rechecked the reversible-surprise action question against
`sim/action_identifiability_result.json`: passive observations are identical
while preferred actions oppose in `40/40` pairs. Therefore that same passive
memory law cannot derive `act`; it needs an intervention model and an outcome
ordering. H027 reached budget `3/3` without its L2 gate (`9.6186 < 13.2814`)
and is parked in `shared/hyp.py`.

## 2026-10-23 — Context-addressed active/dormant exchange

The current crossover `candidates/contextual_reversible_intervention/` keeps
one active and one dormant conditional transition model per context and
exchanges roles only after observed predictive comparison. I tested whether its
context can recall a returning relation on an aligned lagged stream: 40 seeds,
three 800-step phases A-B-A, 5% transition noise, and the first 40 scored
transitions in each phase. The duplicated source/output bits make the candidate's
parity context equal the explicit context bit; this intentionally tests the
addressing mechanism rather than arbitrary parity collisions. The run gave
first-A MSE `.09873`, B MSE `.12464`, return-A MSE `.07546`, and
return-minus-first `-.02327`; late first-A MSE was `.04582`, confirming that
first acquisition had time to improve. Result: `sim/contextual_reversible_return_result.json`.

Ran `nice -n 15 .venv/bin/python -I sandbox/judge.py
candidates/contextual_reversible_intervention --author odkrywca_axioms`.
L1 scored `21.9849`, robustness `.9772`, and highest passed level `0`, below
the `26.2446` gate. The previous recorded L1 was `21.9816`, so the main metric
rose only `.0033`; the benchmark result still does not transfer the toy return
advantage. AST multiplier remains `.4315` from 37 numeric literals and 86
physical lines. Keep one final budget turn; test a simpler formulation only if
its reduced state/update follows from the same context-recall principle.

## 2026-10-23 — Context-addressed reversible-equivalence crossover

Created `candidates/contextual_reversible_equivalence/` from
`contextual_predictive_equivalence` and `reversible_surprise`. Context routes
between active and dormant local transition tables; the dormant table takes
over when its prequential error on an observed transition is lower. The
mechanism description passed `shared/ideas.py check` as new (maximum similarity
`.13`). Searched the same passive-action identifiability result for the
`reversible_surprise` maturity check: 40/40 paired worlds had identical passive
streams and opposite best actions, so this principle cannot derive `act()`.
No action heuristic was added.

Ran `nice -n 15 .venv/bin/python -I sandbox/judge.py
candidates/contextual_reversible_equivalence --author odkrywca_axioms`.
L1 scored `11.2033` with robustness `.9924`, highest passed level `0`, against
the `26.2446` gate. This is below both the gate and the previous crossover's
`21.9849`; no measured benchmark improvement. Result: `sandbox/leaderboard.jsonl`.

## 2026-10-23 — Action derivation boundary

Reran `nice -n 15 .venv/bin/python -I
theory/theorist_axioms/sim/action_identifiability.py`. Across 40 paired
worlds, every passive stream was identical while the optimal interventions
were opposite (`passive_pairs_equal=true`, `worlds_choose_opposite_actions=true`,
mean passive difference `0`). Thus reversible surprise, which only stores
passive conditional predictions, cannot determine an action preference.
The existing `act()` chooses the highest predicted bit among indices 0–3;
those indices are not direction features in Snake, and the mapping does not
follow from the exchange rule. The previously recorded Snake result was
L3 `3.4069` (Journal/H017 history); the calibration restarted in this turn was
interrupted and is not a result. A principled action needs both action-conditioned
causal evidence and an internal ordering over consequences, neither supplied
by reversible surprise. Keep H017 open for its A-B-A memory claim only.

## 2026-10-23 — Reversible-surprise maturity check

Extended `sim/reversible_surprise_return.py` to score equivalent first and
return windows on the null stream, then ran `nice -n 15 .venv/bin/python -I
theory/theorist_axioms/sim/reversible_surprise_return.py`. Across 40 seeds,
first-A late-window MSE was `.236746`, the first 80 steps after return to A had
MSE `.213153` (gain `.023593`). Null first/return MSE was `.228295`/`.221370`
(gain `.006926`), so the paired target-minus-null gain was `.016667` and
return was faster in `.625` vs `.475` of seeds. This passes the registered
`.01` incremental-gain criterion in this toy stream; it supports retaining
H017 as a memory hypothesis, not general competence. Artifact:
`sim/reversible_surprise_return_result.json`.

The same law does not derive `act()`. In the paired identifiability test,
passive observations were identical in 40/40 pairs while the best actions were
opposite in 40/40. The candidate's current highest-predicted-bit action is
not implied by surprise-triggered model exchange. No action was added and no
new judge run was warranted. The missing condition is an endogenous ordering
over consequences, grounded in action-conditioned evidence; prediction and
memory alone leave that ordering unidentified. Keep the Snake claim refuted
while the A-B-A memory claim remains testing.

The contextual predictive-equivalence direction used its third budget turn
without progress: `contextual_reversible_equivalence` scored L1 `11.2033`,
robustness `.9924`, level `0`, below gate `26.2446`. H028 remains parked.

## 2026-10-23 — Context-addressed reversible-error crossover

Created `candidates/context_error_reversible_memory/` from
`contextual_reversible_equivalence` and `reversible_predictive_exchange`.
Context addresses a retained pair of local transition models; per-output
prequential error selects which predictor is active and receives updates.
`python3 shared/ideas.py check` reported NEW (maximum similarity `.08`).

The 40-seed, 500-step A-B-A test used an explicit two-bit observable context
label and a null stream. First-A MSE was `.272053`, return MSE `.274539`, and
paired target-minus-null return gain was `-.0009005`; it did not meet the
`.01` criterion. The mechanism therefore did not survive this memory test.
Artifact: `sim/context_error_reversible_return_result.json`.

Ran `nice -n 15 .venv/bin/python -I sandbox/judge.py
candidates/context_error_reversible_memory --author odkrywca_axioms`.
L1 was `17.4787` versus gate `26.2446`, robustness `.9703`, learning
improvement `.01908` versus `.05`; highest level 0. H031 was registered and
refuted. No action was added: passive prediction still does not identify an
ordering over consequences. H017's earlier paired gain `.016667` remains
testing; this crossover is a separate negative result, not evidence against
that prior result.

## 2026-10-23 — H017 corrected-channel recurrence check

The previous A-B-A harness had an indexing defect: phase A wrote its correlated
value to `values[0]`, then constructed the observation from `values[1:]`. The
scorer consequently evaluated observation index 0 (the source) rather than a
learned source-output relation. Its target-minus-null gain of `.016667` was not
evidence of returned relational memory.

Added `sim/reversible_surprise_valid_return_sweep.py`, with A mapping source to
observed output 1, B mapping source to output 2, and A returning to output 1.
Forty seeds, 500-step A phases, and B gaps of 100, 500, and 1,500 steps gave
paired target-minus-null return gains `-.013697`, `-.004779`, and `-.012571`
MSE. Positive gains occurred in `.40`, `.50`, and `.40` of seeds. Thus the
registered `>.01` memory criterion fails; H017 was parked. Results are in
`sim/reversible_surprise_valid_return_sweep_result.json` and the registry.

Maturity check: reversible surprise still cannot imply a useful `act()`. Its
state predicts passive consequences but contains no intervention-outcome
ordering; the paired identifiability experiment has identical passive streams
and opposite optimal actions in 40/40 pairs. Do not add an action heuristic to
this law or send it to Snake.

## 2026-10-23 — Joint context-level recall crossover

### Mechanism and novelty
Created `candidates/context_joint_recall/` as a mutation of
`contextual_predictive_equivalence` crossed with `reversible_surprise`. A
sensory context addresses two joint transition models; after each complete
next observation, the model with lower aggregate prequential error becomes
active and alone receives the update. This makes retrieval one context-level
exchange instead of separate per-channel swaps. `ideas.py check` returned NEW
(maximum similarity `.19`). Registered H036.

### Results and conclusion
Ran `nice -n 15 .venv/bin/python -I
theory/theorist_axioms/sim/context_joint_recall.py` on 40 seeds and 500-step
A-B-A phases. First-A MSE was `.060638`, return-A MSE `.068640`, and paired
null-adjusted return gain `-.003425`; return was faster in `.40` of seeds.
The memory claim failed. Full judge L1 scored `16.1494`, robustness `.9271`,
highest level `0`, below gate `26.2446`; H036 is refuted. Artifacts:
`sim/context_joint_recall_result.json` and `sandbox/leaderboard.jsonl`.

### Action derivation
The same-principle maturity question for `reversible_surprise` remains
negative. In `sim/action_identifiability_result.json`, passive observations
were identical while optimal interventions were opposite in 40/40 pairs.
Prediction and context recall contain no ordering over consequences; adding
`act()` would require another axiom, and no action heuristic was added.

## 2026-10-23 — Context-conserved predictive flow crossover

Crossed the top coactivity source-mass candidate with `resource_flow_memory`.
The mutation keeps local relation support in context-addressed banks and lets
prediction-derived flow set the local update rate. The novelty checker returned
NEW (maximum similarity `.09`). Parents and rationale are recorded in
`candidates/context_conserved_predictive_flow/PARENTS.txt`; H038 is registered.

Ran `nice -n 15 .venv/bin/python -I
theory/theorist_axioms/sim/context_conserved_predictive_flow.py` on 40 seeds
with 500-step A-B-A phases and matched nulls. First-A MSE was `.259662`,
return-A MSE `.265906`, return-minus-first `+.006244`, and paired null-adjusted
gain `-.001445`; only `.40` of seeds returned faster. The test can expose a
return benefit: it compares equally sized 80-step windows after 420 samples of
first A learning versus immediately after 1,000 intervening observations.
The effect failed its `>.01` return criterion. Artifact:
`sim/context_conserved_predictive_flow_result.json`.

The full judge gave L1 `22.8067`, below gate `26.2446`, with `R=.9521` and
highest level 0. H038 is refuted; result is in `sandbox/leaderboard.jsonl`.
The context-memory direction has now used its three-turn budget without a
positive null-adjusted return gain, so it is parked. Maturity answer remains
negative: `reversible_surprise` cannot derive an `act()` because identical
passive histories admit opposite action optima in 40/40 pairs; its law lacks
action-conditioned evidence and an endogenous ordering over consequences.
No action was added.

## 2026-10-23 — Prediction-error-addressed context

Created `candidates/predictive_error_context/` as a crossover of the three
requested island candidates. Local transition evidence is addressed by a
bucketed signature of prior prediction errors, with a shared global model as
fallback. `ideas.py check` returned NEW (maximum similarity `.11`); H053 was
registered and refuted by its memory criterion.

Ran the matched 40-seed A-B-A test with 500-step phases. First-A MSE was
`.248770`, return-A MSE `.246618`, and null-adjusted gain `-.000458`; the
positive return-minus-first difference (`-.002152`) did not beat the
independent null. This test has enough exposure to show return: first A has
500 samples and the return window starts after 1,000 intervening observations.
Artifact: `sim/predictive_error_context_return_result.json`.

The judge passed L1 (`27.3622`, `R=.9951`) and L2 (`16.8891`, `R=.9817`),
then stopped at L3 because the candidate has no `act()`. Overall reported
score is `16.8891`; see `sandbox/leaderboard.jsonl`. Prediction-error context
did not improve A-B-A memory over null, so one remaining turn is budgeted for
this direction before parking it.

## 2026-10-23 — Consequence-gated persistence crossover (H057)

The next axiom was that a relation's returned predictive consequence is its
own persistence currency: signed evidence still adapts online, while the
relation's persistence mass grows only with local predictive consistency
`2/(1+error^2)-1`. The novelty check was NEW (maximum similarity `.12`).

The 40-seed A-B-A test (`sim/consequence_gated_return.py`) compared 80-step
windows after 500-step A exposure and gaps 100, 500, and 1,500 against a
matched null. Paired target-minus-null gains were `-.01293`, `-.00328`, and
`-.00208`; the memory criterion is therefore not established. The test can
expose return but this rule does not improve it in this harness.

The compact world-agnostic candidate nevertheless transferred strongly:
`candidates/consequence_gated_return_flow/principle.py` scored L1 `53.3287`,
`R=.9917`, above `resource_flow_local_return` (`52.9624`). Prediction skill
was `.25233`, return-memory component `.04875` versus `.04434`, and the
learning gate passed. This is a judge result, not evidence that A-B-A memory
is solved; keep H057 testing for a second turn focused on a real dormant
address rather than another persistence-weight variant.
