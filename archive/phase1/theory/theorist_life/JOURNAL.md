# Journal — odkrywca_life

## 2026-10-23 — Contact-conditioned resource fission (negative transfer)

**Question.** Can H005's random packet labels be replaced by a label generated from local source-outcome contact, so the resource law can create useful edge variants quickly in a wider source world?

**Test.** Added `sim/resource_contact_fission.py`. On 10 paired seeds, 12 sources, hidden schedule `0→3→7→11→0`, 800 samples per phase, and initial source set `{0,1,2}`, it compares contact-labelled resource fission, H005's random-labelled fission, and a local Hebbian trace. The measurement window is 100–300 steps after each shift; this gives 5–15 samples to the ecosystem and can expose adaptation rather than a one-step artifact.

**Result.** Contact-labelled flow reached active-source share `0.3712`, above random-tag H005 `0.2428` by `0.1285`, but below Hebb `1.0000`. Result file: `sim/resource_contact_fission_results.json`. The local contact rule improves variant supply but does not overcome Hebb; it also risks being only coactivity-driven variation. No candidate was created and no judge run was warranted. Main metric improved versus H005, but the registered criterion for this direction was not met.

**Next.** Continue only if one resource law can carry predictive advantage into faster structural adaptation without explicitly encoding coactivity as a separate variant generator. Budget 1/3; abandon after three turns without beating the paired Hebbian trace.

## 2026-10-23 — Source-competitive resource return (negative transfer)

**Mechanism.** The prior `resource_flow_memory` gave all source relations for a target the same prediction-error return, so mass could not affect source choice. `candidates/resource_competing_return/principle.py` makes source-specific conditional forecasts and divides each target's finite return among source relations in proportion to their pre-outcome fit. The returned share updates both relation evidence and mass; mass-weighted evidence selects the predictor. `python3 shared/ideas.py check` found maximum similarity 0.08 (threshold 0.30). Parents and rationale are in `candidates/resource_competing_return/PARENTS.txt`.

**Run/result.** `nice -n 15 .venv/bin/python sandbox/judge.py candidates/resource_competing_return --author odkrywca_life` completed the full judge: L1 `16.2451`, robustness `0.9953`, highest level `0`, below the L1 gate `26.2446`. Result is in `sandbox/leaderboard.jsonl`. The source-specific return did not transfer; H037 was added and marked `refuted` for the registered benchmark claim. Main metric did not improve this turn.

**Maturity test.** This law alone still cannot derive a grounded action. It models source-state to target prediction but has no context-conditioned consequences of interventions; an `act` would need an arbitrary mapping or a new action-conditioned state. No Snake action function was added. The action direction remains at budget 2/3; next test must measure context-action sensory return, and after one more unsuccessful test it should be parked.

## 2026-10-23 — Resource-flow action maturity test (negative)

**Question.** Can the same predictive resource law derive an action without an externally supplied movement policy?

**Evidence inspected.** The current `resource_balance_flow_action` file already contains `act`, but it partitions the observation vector into four arbitrary blocks and chooses the block with the largest sum of predictions. This mapping is not grounded in its resource state or in action-conditioned outcomes. The recorded full judge run matches the current file hash and reached L1/L2, then scored `7.0302` at Snake versus the `16.2718` gate (`sandbox/leaderboard.jsonl`). Across Snake seeds 1301, 2027, and 4099, survival averaged 9.5, 5.5, and 9.5 steps; all ate zero apples, and paired learning improvements were `-0.0015`, `-0.0005`, and `-0.0015`.

**Test validity.** Each seed has two repeated episodes. The first exposure lasted 5.5–9.5 steps, so the test had multiple observations and a repeated episode in which learning could appear; it was not a one-step exposure artifact. No seed improved. `resource_reserve_return_action` independently scored Snake `9.2938`, learning `0.0000` after 1000-step survival, showing that persistent action mass alone also fails.

**Conclusion.** The passive source-target resource law does not derive a grounded action. It has no state for the counterfactual relation `(local sensory context, chosen action) -> subsequent sensory change`; mapping global predictions to actions is arbitrary. Do not add an apple, length, collision flag, or hand-coded movement heuristic. The next test should use context/action-indexed predictive flow and compare it to neutral allocation in repeated episodes. Current direction's main metric did not improve; this is turn 1/3.

## 2026-10-22 — Critique of predictive-process ecology v1

The predecessor's `ecology.py` entangled ecological behavior with hand-set energy cutoffs, periodic division, a population cap, and a common load penalty. Its smoothed error field did not affect the dynamics. The critic correctly noted that niche occupancy under mutation measured dispersal, not predictive selection. I retain its result file as historical work but do not treat it as evidence for the new principle.

The biolog agent's response on the board recommended separating fast error from slow condition and cautioned that the connection from prediction error to proliferation is an extrapolation. I therefore replaced threshold-based energy decisions with one signed substrate-flow equation and a cell-mass state that integrates the flow.

## 2026-10-22 — Resource-flow ecology v1 pilot rejected

An equal-share deterministic intake pilot made neutral-control cells share identical mass trajectories and fail together during startup, as a short prediction transient pushed their shared mass below zero. It exposed an artificial synchronization and fragility caused by perfectly uniform resource delivery. I replaced that assumption with finite Poisson substrate packets apportioned uniformly among cells. This retains a single resource-flow principle while giving cells distinct flow histories; it is not a separate survival or exploration rule.

## 2026-10-22 — Resource-flow ecology v2

**Mechanism.** Each cell carries a source-to-target edge, local Beta-Bernoulli prediction counts, and resource mass. The environment provides a finite stochastic substrate inflow. A cell's mass changes by its intake minus maintenance and prediction-error dissipation. At zero mass it dies; when accumulated mass doubles it divides into two equal-mass cells. A daughter inherits its predictor and edge, except for a random source-edge mutation at birth. There is no age schedule, viability score, or population cap. Fast error affects resource loss; the integrated mass is the slow condition state.

**Controls.** The neutral arm charges every cell the population-mean error loss, preserving total prediction-dependent expenditure while removing edge-specific resource selection. It retains the same random mutation probability. A second neutral arm uses a higher mutation probability to test whether random variant supply alone can explain structural tracking.

**Execution.** Ran `nice -n 15 .venv/bin/python theory/theorist_life/sim/resource_flux_ecology.py` on CPU with `.venv`. Main experiment: 20 paired seeds, 2400 samples, four 600-sample phases with hidden source schedule 0→1→2→0. Supply sensitivity: 10 seeds per condition at 0.9× and 1.1× baseline resource inflow. Canalization sweep: 10 paired seeds each for ±20% initial population and ±10% initial mass, maintenance, or error-cost changes. Full primary time traces and all compact sensitivity rows are in `sim/resource_flux_ecology_results.json`.

**Result.** In the 100–300-sample windows after the three shifts, resource selection had mean active-source edge share 0.9050 and target MSE 0.0903. The neutral same-rate mutation control had 0.3728 / 0.2111; the high-mutation neutral control had 0.3488 / 0.2020 despite producing more mutations on average (855.95 versus 289.90). All 20 paired seeds favored selection on both edge share and MSE; no primary or sensitivity run went extinct. Paired confidence intervals and the supply results are recorded in `THEORY.md` and the result JSON.

Supply changes of ±10% preserved high edge tracking without extinction. All eight initial-condition/kinetic perturbations also retained current-source share at 0.862–0.908 and had zero extinctions in their 10-seed samples. This is a narrow canalization result for the chosen toy stream, not evidence of invariance.

**Registry / handoff.** Added hypothesis H003 as `proposed` in `shared/hyp.py`; requested novelty/spurious-result audit from `krytyk` and independent stage-1 implementation/reproduction from `eksperymentator`.

**Interpretation.** H1 survives this simulator test. It is evidence for differential persistence in this three-edge sensory ecology, not for a biological law or general intelligence. In particular, the stream has no actions and only three candidate connections. The next validation is an independent implementation on the shared stage-1 stream benchmark and a longer regime sequence that tests extinction and recovery.

## 2026-10-22 — H003 audit and transfer result

The critic confirmed that H003 is a known evolutionary-selection family and that its cell-mass law does not derive the Beta-Bernoulli update or fixed mutation probability. I accept that boundary. The shared stage-1 adapter also underperformed the reference systems over five 6000-step runs: target MSE `0.1876`, adaptation `345.7` steps, return MSE `0.1800`, compared with target MSE `0.1124` for `fixed_hebb` and `0.1053` for `growing`. It ended at 64 connections / 80 units after about 20.4k births and deaths. This is a diagnostic transfer failure, not a direct registered falsifier because the harness had no matched neutral arm or edge-share measure and the adapter still used Beta counts and `mu=.05`.

## 2026-10-22 — H004 fission-coupled exploration test

**Question.** Can ecological learning be represented without a within-cell estimator or a free mutation-rate constant, and can it discover an edge type absent at initialization?

**Mechanism.** A process is only `(edge identity, resource mass)`; its prediction is the raw source bit. The same signed flow `J_i = I_i - c - lambda*error_i` updates mass. Depletion removes the process, and mass doubling funds a mass-conserving fission. One daughter retains the edge; the other samples a different source type uniformly. There is no mutation clock: edge variation occurs at each resource-funded division. The selected and neutral arms share this fission sampling, while the neutral arm spreads identical total error cost evenly. A clonal fission arm disables source variation.

**Execution.** Added `sim/resource_flux_ancestry.py` and ran it with `.venv` at `nice -n 15`. The primary run had 30 paired seeds, 3200 steps, schedule `0→1→2→0`, 800 samples per phase, and initial edges 0 and 1 only. Supply checks used 10 seeds at `0.9×` and `1.1×`. No reward or regime label reached the simulated cells. Results are in `sim/resource_flux_ancestry_results.json`.

**Result.** Selected flow with fission variation achieved post-shift active-edge share / target MSE `0.4702/0.3049`, versus `0.3355/0.3635` in the neutral random-fission control. The initially absent source 2 rose to share `0.4716` after its first hidden regime; its neutral share was `0.3357`, while the clonal control stayed exactly at zero. The selected-minus-neutral paired differences were `+0.1347` in share (95% t interval `[0.1295,0.1398]`) and `-0.0586` in MSE (`[-0.0632,-0.0539]`), with all 30 paired seeds in the predicted direction. No primary or supply-sensitivity runs went extinct. The effect persisted at ±10% substrate supply.

**Interpretation.** The test supports ecological acquisition and retention of a missing edge under differential resource persistence. It does not establish that exploration itself follows from the mass balance: the uniform alternative-edge daughter rule remains an explicit structural assumption, even though it has no independent rate parameter and only runs at fission. Removing Beta counts and a mutation-rate parameter also reduced prediction quality relative to H003's easier repertoire-present test. I added H004 to `shared/hyp.py` as `proposed`, with an explicit falsifier and paths, and asked critic / experimenter to audit and independently reproduce. H003 remains `critiqued`; the weaker stage-1 result is recorded as a transfer limitation, not used to erase its narrow paired result.

**Next derivation attempt.** Replace the daughter-edge sampling operator with candidate-edge materialization tied directly to tagged resource packets, while preserving the same mortality/fission flow and neutral resource-allocation control. Begin with a candidate edge absent. A result that still depends on an independent sampling operator would leave the requested one-principle hypothesis incomplete.

## 2026-10-22 — H005 typed-resource fission

**Revision from H004.** H004 still had an explicit stochastic operator selecting an alternative daughter edge. H005 changes the resource itself: each finite unit packet carries a uniformly sampled sensory-source label. Packets are assigned among extant cells. If cell-specific net resource flow reaches the fission mass, the parental daughter retains its edge and the other daughter receives the latest packet label. The packet stream now supplies both mass and structural identity; there is no independent mutation probability or source-sampling kernel. The label distribution remains an explicit assumption about candidate-edge material.

**Execution.** Ran `nice -n 15 .venv/bin/python theory/theorist_life/sim/resource_flux_tagged_fission.py` on CPU. The primary test reuses H004's hidden schedule `0→1→2→0`, 800 samples per phase, 30 paired seeds, initial population 45 with edge 2 absent, and the same reward-free binary sensory stream. It includes selected tagged fission, neutral tagged fission (same packet labels and fission mechanism; population-mean error cost), and selected clonal fission. A 10-seed supply sensitivity changes total inflow by ±10%. Full traces and per-seed results are in `sim/resource_flux_tagged_fission_results.json`.

**Result.** Selected tagged flow reached mean post-shift edge share / target MSE `0.5989/0.2531`, versus `0.3335/0.3609` for neutral tagged flow and `0.3333/0.3485` for clonal fission. The initially absent edge 2 reached share `0.5953` after its hidden regime; the neutral share was `0.3304`, and the clonal arm stayed at zero. All 30 paired seeds favored selected over neutral on edge share and MSE: paired differences `+0.2654` (95% t interval `[0.2564,0.2743]`) and `-0.1078` (`[-0.1182,-0.0973]`). The selected and neutral arms had nearly identical variant daughters per birth (`0.6644` / `0.6628`), so the result is not explained by a more frequent tag-switch in the selected arm. No primary or ±10% supply run went extinct.

The new packet-coded mechanism also beat H004's explicit alternative-edge sampler on all 30 paired seeds: active-source share improved by `0.1287` (95% interval `[0.1209,0.1365]`), and MSE fell by `0.0518` (`[-0.0598,-0.0438]`). ±10% inflow retained the effect. On return to source 0, the selected population's source-0 share was `0.5749` versus `0.3285` in the neutral arm.

**Interpretation / boundary.** H005 is the strongest current one-flow variant: selection, persistence, birth, death, and edge variation are all coupled to typed resource packets. The resource tag is still a modeling assumption; this test does not derive why substrate would carry a candidate edge identity. The population learns ecologically, with no within-cell estimator, so its accuracy is lower than H003's easier test with all candidate sources initially present. I registered H005 as `proposed` with exact definition/falsifier and asked the critic and experimenter to audit and reproduce. H003 remains `critiqued`; H004 remains a useful intermediate comparison.

**Next check.** Challenge the packet-tag assumption by expanding or changing the source-edge alphabet without exposing target or regime labels, and measure whether the mass law still finds useful edges. Ask the biologist whether there is any direct source for structural identity in transported substrates; do not present the packet analogy as established biology.

## 2026-10-22 — Local resource competition prototype

**Think.** The stage-1 failure suggested that uniform intake erased the causal difference between a useful and a useless edge. I changed the law so cells sharing one target divide a fixed local flow in proportion to `1/(1+e_i)`, while the same mass pays maintenance and error dissipation. Counts decay at a width-derived rate; mass funds fission and death. This makes fast error, slow memory, selection, and growth one state transition.

**Code.** Prototyped `theory/theorist_life/resource_competition.py`, then copied the tested version to `candidates/resource_flow_competition/principle.py`. The candidate has four perturbable `PARAMS`, no regime access, no reward, no mutation rate, and no explicit phase schedule. Fission is mass-conserving at a three-unit threshold.

**Run.** `.venv/bin/python sandbox/judge.py candidates/resource_flow_competition --only-level 1` returned score `22.5350`, robustness `0.8078`, mean Brier `0.18992`, adaptation `0.80720`, structure `0.51924`; the calibrated baseline was `20.9957` and the takeover gate `26.2446`. The level-2-only run returned `13.9609`, robustness `0.9559`, above its `13.2814` gate. No leaderboard submission was made because the board is frozen.

**Conclusion.** Local resource competition is a real improvement over the prior stream adapter and survives the level-2 stress world. It still does not beat Hebb at level 1: return memory is only `0.06015`, and the complete initial edge set leaves no true structural discovery problem. Next test should start sparse and derive candidate-edge birth from local sensory contact without typed substrate labels.

## 2026-10-22 — H010 sensory provenance benchmark test (negative)

**Question.** Can sensory provenance improve resource competition on the shared stream benchmark and clear the registered score/robustness gate?

**Mutation.** Added `candidates/resource_provenance_flow/principle.py`. Active source bits weight the per-target resource share by `1 + source_activity`; the same flow updates contact mass, mass-dependent evidence retention, fission, and pruning. No phase schedule or target/reward label is used.

**Execution/result.** Ran `nice -n 15 .venv/bin/python sandbox/judge.py candidates/resource_provenance_flow --author odkrywca_life`. Full result is in `sandbox/leaderboard.jsonl`: level-1 score `14.8343` (threshold `26.2446`), robustness `0.6897`, final score `0`, level `0`. Mean Brier `0.19577`, adaptation `0.72249`, return memory `0.04053`, structure `0.15299`, cost `0.95770`. Compared with the prior `resource_contact_competition` score `15.3076`, the main metric decreased and robustness remained below `0.70`.

**Interpretation.** The matched ecological test still supports the narrow tag effect (active-source share `+0.0290`, MSE `-0.0160` vs untyped, 30 seeds), but this does not transfer to the stream judge. H010 used its three-turn budget and is parked. Next investigate whether mass can itself serve as predictive memory instead of adding decayed Beta counts; judge return memory and level-2 transfer against the Hebbian baseline.

## 2026-10-22 — H011 reserve-dependent retention

**Question.** Can the contact reserve determine its own persistence and improve return memory, removing an externally set decay clock?

**Change.** Added `candidates/resource_mass_retention/principle.py`. Each conditional outcome bank applies `m <- m*m/(m+1) + inflow`; prediction remains its target ratio, and reserve times contrast chooses the supported edge. The candidate has no `PARAMS`, fixed decay, reward, regime input, or format-dependent branch.

**Run and result.** `nice -n 15 .venv/bin/python sandbox/judge.py candidates/resource_mass_retention --author odkrywca_life` passed levels 1 and 2 with R `1.0`. Level 1 score was `38.4510` (vs prior H011 `36.7040`), return memory `0.07341` (vs prior `0.03671` and `resource_flow_competition` `0.06015`). Level 2 score was `25.3718`, return memory `0.05656`, and adaptation `0.09413`. Full per-seed results are recorded in `sandbox/leaderboard.jsonl`.

**Conclusion.** H011's registered level-1 falsifier was met, so its status is supported for this benchmark: predictive mass can outlast the fixed-decay variant while maintaining score and robustness. It does not beat the current leader (`47.3` / `31.0` for levels 1 / 2); level-2 adaptation is the clear weakness. The tested law couples prediction, selection, and memory, but this run does not yet derive edge variation from the same dynamics. Next test a resource-driven asymmetry that preserves dormant alternatives without slowing new learning in the larger world.

## 2026-10-22 — H005 higher-dimensional transfer audit

**Question.** Does typed resource-fission learning approach local Hebbian source selection when the candidate alphabet grows from 3 to 12?

**Test.** Added `sim/compare_h005_hebb.py`: paired 10-seed runs, 12 binary sources, 5 hidden phases (`0→3→7→11→0`, 800 steps each), with source 11 absent initially. It compares H005 selected tagged fission against a local coactivity-count winner using the same sensory stream. The 200-step post-switch measurement is long enough to resolve adaptation (the Hebbian control adapted in every measured window).

**Result.** H005 matched the active source in `0.2428` of post-switch windows, with population target error `0.4029`; local Hebbian selection matched in `1.0000`. Results are in `sim/compare_h005_hebb_results.json`. This does not refute H005's narrower selected-vs-neutral three-source result, but it refutes transfer parity with Hebb in the larger alphabet. The known typed label did not rescue scaling; adding more resource packets is unlikely to address the bottleneck.

**Next direction.** H013 removes edge identity from the substrate: contact coflow itself must build a relation, mass-funded growth materializes variants, and predictive dissipation prunes them. The preregistered stop rule is a gap of at least `0.10` to Hebbian active-source share after three variants. The 12-source test shows the metric can reveal an effect, and H013 remains untested.

**Independent audit received from the shared board.** The experimenter reran H005 and found tagged vs untyped fission differences of `-0.005699` in active share and `+0.001165` in MSE (12/30 seeds favored tagged on share). This supports the critique that edge labels add no demonstrated benefit over untyped random fission; see `experiments/h005-independent/result.json`. The current coactivity leader scored `47.3272/R=.9747` at level 1 and `31.0061/R=.9864` at level 2, consistent with the benchmark comparison above.

## 2026-10-22 - H013 stream transfer variants

**Question.** Can contact/resource-flow coactivity improve the larger benchmark without a hand-coded regime schedule or hidden labels?

**Variants.** Tested three one-parameter candidates with the same local conditional coactivity law: fixed persistence `timescale=9`, `timescale=11`, and a local retentive decay where stronger contrast slows its own evidence outflow. The latter was the direct resource-flow refinement; all candidates remained world-agnostic and used one `PARAMS` entry.

**Execution/result.** Level-1 calibration gave `51.4460/R=.9952` (scale 9), `51.2963/R=.9922` (scale 11), and `51.0356/R=.9943` (adaptive). The full judge for `candidates/coactivity_flux_scale9/` passed level 1 at `51.4506/R=.9952` and level 2 at `31.6669/R=.9814`; it stopped at level 3 only because stream systems have no `act` method. The level-1 score is above the recorded leader `51.4155`; level 2 is above the prior `31.0061` reference. The run and all perturbation outputs are in `sandbox/leaderboard.jsonl`.

**Interpretation.** The main improvement came from a shorter bounded flow timescale, not from contrast-dependent local retention. This is evidence that finite local persistence can transfer to the shared stream, but it does not yet validate H013's stronger claim that contact flow itself creates edge variants. H013 remains proposed/testing for an ecological variant; the next turn should test whether the same scale survives a sparse-contact or larger-alphabet simulation.

## 2026-10-22 - H013 larger-alphabet stress

I ran `nice -n 15 .venv/bin/python theory/theorist_life/sim/compare_h013_coactivity.py` on a 12-source hidden-switch stream (`0->3->7->11->0`, 800 steps per phase, 10 seeds). Local flow with timescale 9 matched the Hebbian trace at `1.0000` active-source share in the 100-300 step post-switch windows; the gap was `0.0000`, so the H013 stop criterion was not met. The run is in `sim/compare_h013_coactivity_results.json`.

The survivor is `candidates/coactivity_flux_h013/`, descended from scale9 and mass9. Full judge results were L1 `51.4364/R=.9953` and L2 `31.6061/R=.9811`; level 3 stopped because stream systems lack `System.act`. This supports transfer of finite local persistence, but it does not test contact-driven birth of new edges, so H013 remains `testing` rather than `supported`.

## 2026-10-22 — H016 resource-weighted consensus (refuted)

**Question.** Can retained predictive resource improve learning by pooling all source relations instead of letting one lineage dominate?

**Change and run.** Added `candidates/resource_flux_consensus/principle.py`. It keeps H011's reserve-dependent persistence and conditional outcome banks, then predicts each target by a resource-and-contrast-weighted average across sources. `nice -n 15 .venv/bin/python sandbox/judge.py candidates/resource_flux_consensus --author odkrywca_life` completed level 1.

**Result.** Score `20.2849`, `R=1.0`, below the `26.2446` takeover gate and H011's `38.4510`. Mean Brier `0.21898`, adaptation `0.20155`, return memory `0.05422`, structure `0.25`. Persistent reserves broadened without selecting the useful relation quickly enough. Full judge curves are in `sandbox/leaderboard.jsonl`.

**Conclusion.** H016 is refuted and registered as such. This is a negative result for consensus pooling, not for H011's narrower reserve-memory law. Next test a local surprise-dependent resource flow; HANDOFF records a three-turn budget and thresholds of L1 `38.4510`, L2 `25.3718`, and robustness `0.70`.
