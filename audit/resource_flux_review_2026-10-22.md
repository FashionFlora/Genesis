# Review of the resource-flow ecology candidate

Scope: theory/theorist_life/sim/resource_flux_ecology.py and its result file, theory/theorist_life/sim/resource_flux_ecology_results.json. This candidate is not registered in hyp.py, and theory/theorist_life/THEORY.md and JOURNAL.md still describe only the older viability-selected predictor. I therefore review it as an emerging candidate, not as a registered hypothesis or a literature priority claim.

## Prior-art verdict: a known evolutionary selection principle, with a distinct implementation

The code implements heredity, variation, and differential reproduction: daughter cells inherit a source connection and predictor counts; a fixed-probability mutation changes the connection at birth; prediction error reduces resource mass and therefore survival/reproduction. That is a direct instance of Darwinian selection over predictive variants, with shared finite resources supplying competition.

Shvartzman and Ram (2024), “Self-replicating artificial neural networks give rise to universal evolutionary dynamics,” PLOS Computational Biology 20(3):e1012004, opened in full at PMC11003675, already study self-replicating neural networks whose task performance determines fertility and whose offspring inherit mutated genotypes. Their mutation process arises from imperfect self-copying and their task network uses standard deep-learning training; this differs from the candidate's explicitly random connection mutation and local online sensory prediction error as resource cost. It establishes close prior art for the population-level self-replication/selection framing, not exact identity with this resource-flow model. The candidate is not an explicit free-energy, maximum-entropy, or empowerment objective. Its broad governing idea is evolutionary selection, already known.

The current code is also a refinement of theorist_life's own version-1 ecological predictor: both let local prediction fit affect persistence and reproduction. Version 1 used a smoothed energy state, separate survival/division thresholds and an age gate; this version replaces those demographic controls with integrated mass flow, depletion death, and binary fission. That is a meaningful simplification of the demographic rule, but not evidence that learning, memory, and exploration now follow from the same law.

## What actually follows from the mass-flow rule?

For cell i, the net mass increment is I_i minus maintenance m minus lambda times the prediction error. Summing this into cell mass, deleting cells at nonpositive mass, and splitting mass at two units makes growth and death consequences of a shared demographic state. The finite inflow and random apportionment create resource competition without a population cap or global ranking.

Other claimed phenomena remain separate mechanisms:

- Learning is a Beta-Bernoulli conditional-frequency predictor with explicit unit pseudocounts. The flux does not update these predictive counts.
- Memory is the predictor's count state, copied to offspring. This is inheritance of a separately defined learner state, not a derived property of resource flow.
- Exploration is an explicit mutation probability at division, currently 0.05, with the daughter choosing uniformly among the other fixed source channels. The rate and mutation distribution are supplied by the modeler rather than derived from the flux.
- The candidate set is a fixed three-source repertoire. Cells copy one source-to-target connection; population growth duplicates cells and does not create new endpoint types or intra-network synapses. The experiment starts with all three source types represented, so it does not test discovery of a missing type.

The dynamics still depend on explicit quantities: initial population 45, Poisson resource inflow 7.3125, maintenance 0.10, error cost 0.25, mutation rate 0.05, and the unit-mass convention that makes death occur at zero and fission at mass two. The inflow is set to exactly balance the initial population at mean Brier error 0.25: 45 × (0.10 + 0.25 × 0.25) = 7.3125. This is a transparent baseline calibration, not a hidden leak, but should be treated as a designed operating point. The ±10% supply sensitivity is useful and should be retained.

## Test audit

The primary experiment uses 20 paired seeds, three possible source types, and four 600-step phases with active source schedule 0→1→2→0. The active-source schedule generates observations and is written to the evaluator trace; cell prediction and resource updates use only source-channel observations and the target sensory bit. The main condition and neutral_random_mutation both use mutation rate 0.05 and the same environment/resource RNG seeds. The control replaces each cell's individual prediction-error cost with the population mean, preserving the same total error cost while removing the association between a cell's connection and its reproductive advantage. This is a relevant control for the selection mechanism. I found no task reward, target-index input, task label, or gradient path in the selected update.

Across post-shift trace windows 100–300, selected achieved matching-source fraction 0.9050 (between-seed SD 0.0329) and target MSE 0.0903 (SD 0.0252); neutral_random_mutation achieved 0.3728 (SD 0.0976) and 0.2111 (SD 0.0208). Paired seed differences were +0.5322 (SD 0.1051) for matching fraction and -0.1208 (SD 0.0300) for MSE. These aggregates were extracted from the recorded run-level traces. Neither condition went extinct in the 20 main seeds. At 90% and 110% supply, the selected condition retained mean matching fractions 0.9246 and 0.8902 respectively across 10 seeds per level, with no extinctions. I also reran the 20-seed primary experiment from the current source in memory; its summary exactly matched the saved summary.

Do not use neutral_matched_mutation as the equal-mutation-rate comparison: its rate is 0.15 while selected uses 0.05. It is a separate high-mutation condition. The neutral_random_mutation condition is the matched-rate ablation and is the clean comparison for selection.

The evidence supports a narrow claim that cell-specific predictive error can bias reproduction and source composition under this simulator. It does not establish that resource flux alone produces learning, mutation/exploration, or open-ended neural growth. The result file reports means but not seed-level uncertainty; the per-seed records permit it to be reported. There is no preregistered hypothesis or falsifier, and the current THEORY/JOURNAL do not yet give the resource-flow model formal definitions or a registered claim.

## Recommended next checks

Register a narrow prediction and falsifier before extending the model. Keep the selected versus same-rate neutral control, add mutation-off and no-selection controls, start from a repertoire missing the next active source, and test nonperiodic regime lengths. Report per-seed paired uncertainty, total mass/resource accounting, predictor memory across fission, connection-type counts, and extinction over longer horizons. State separately whether the claimed structure is a population of self-replicating predictors or a growing network; those are different architectural claims.

## Opened source

- Shvartzman, B. and Ram, Y. (2024). “Self-replicating artificial neural networks give rise to universal evolutionary dynamics.” PLOS Computational Biology 20(3):e1012004. Full text opened through shared/lit.py: https://pmc.ncbi.nlm.nih.gov/articles/PMC11003675/

Additional bounded searches through shared/lit.py for evolutionary neural networks with prediction-error-driven reproduction and local structural plasticity returned no search results. The opened SeRANN paper establishes the broad self-replication and selection family; exact identity with this resource equation was not established.

## H003 and robustness-sweep follow-up

The candidate is now registered as H003. Its current theory specifies the finite source stream, Beta-Bernoulli predictor, pre-update Brier error, packet allocation, mass update, fission, inheritance, mutation, controls, and a qualitative falsifier. The registered prediction is appropriately narrower than the original broad unifier claim: resource-selected populations should shift edge share and lower error against same-total-cost neutral controls, including a higher-mutation control, and retain the effect under ±10% supply variation.

The saved result now includes paired 95% t intervals. The source/result timestamps are consistent with the current implementation. The 20-seed test meets H003's qualitative prediction: all paired seeds favor selection against both neutral arms on edge share and target MSE, and the ±10% supply comparisons retain the direction with no extinction. This is useful evidence for the resource-selection component in its simulator. It is still an in-simulator test rather than the independent implementation called for by the falsifier.

The result also adds a ten-seed local parameter/initial-condition sweep (population, initial mass, maintenance, error cost). Function metrics remain in a narrow range, but the sweep has no predeclared tolerance for “stable function” and records no graph distance or topology-divergence metric. It therefore supports a limited sensitivity observation, not yet the stronger canalization claim that function stays fixed while wiring diverges.

The test does not remove the core critique. The resource law drives demographic survival/fission, but the Beta count update and mutation probability/source distribution are separate mechanisms. Resource mass gates when mutation can occur; it does not derive mutation rate 0.05 or the choice of a different source. All three source types are represented at initialization, and the set of possible connections is fixed. The model is best treated as a resource-mediated Darwinian selection experiment, not one law from which learning, memory, open-ended growth, and exploration all follow.
