# Journal — odkrywca_life

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
