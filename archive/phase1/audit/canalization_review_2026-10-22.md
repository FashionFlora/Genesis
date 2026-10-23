# Review of the canalization proposal in biology/PRINCIPLES.md §5

Scope: the observed-biological claims and digital abstraction in §5, plus the proposed perturbation test. This is not a registered hypothesis in hyp.py.

## Prior-art verdict: canalization is an established principle

The broad idea is not new. The opened peer-reviewed paper by Biswas et al. is explicitly titled “Canalization of neural dynamics by δ-protocadherins in the developing zebrafish optic tectum” (PLOS Genetics, 2026). It invokes Waddington's established concept of developmental trajectories being buffered against small genetic, environmental, and stochastic perturbations. The paper provides a specific biological example, not a new general law that all learning phenomena follow from.

The source verifies several biological measurements reported in §5: in nine wild-type larvae, the first five PCA neural modes explain 89.9 ± 1.8% of response variance, and trial-to-trial correlations exceed 0.9 across all five modes. Pcdh19 and Pcdh17 mutants show stochastic deviations from wild-type latent dynamics; the authors discuss allele-dependent severity and possible compensatory mechanisms cautiously.

The source measures evoked population activity and latent neural dynamics. It does not directly quantify each animal's connectome or show that different graph topologies produce the similar wild-type activity. The statement that function is more reproducible than precise wiring is a plausible interpretation of broader biology, but these measurements alone establish conserved dynamics, not observed wiring divergence. The paper's developmental candidate-synapse and persistence account is discussed as a mechanism hypothesis, not isolated by these activity measurements.

## Does canalization derive growth, pruning, learning, memory, and exploration?

No. Canalization describes a robustness property of outcomes across perturbations; it does not specify an update rule. The current formal sketch defines a developing state transition s(t+1)=f_theta(s(t),e(t),xi(t)) and a task-relevant distance d_F, but remains a schema until the task, observable, distance, epsilon, perturbation set Δ, and tolerated failure probability are set. “Low probability,” “small perturbation,” and “stable functional basin” currently have no numerical meaning.

The digital implication in §5 proposes stochastic candidate formation plus biased persistence. That is a known structural-plasticity/selection family and substantially overlaps H001's random coactive sprouting, local evidence, stabilization, and pruning. Section §5 gives no equation deriving those operations from canalization itself. It also does not explain how learning or memory are encoded, how the candidates are generated, or how exploration is made useful. Canalization can be a valuable robustness test for a candidate mechanism, but should not be presented as the mechanism that generates the target behaviors.

There is no explicit FEP, maximum-entropy, or empowerment objective here. The risk is relabeling an established developmental-robustness principle as the project's new unifying rule, then manually inserting stochastic growth and persistence underneath it.

## Status of the proposed digital test

The proposal to perturb initial conditions and inherited parameters while measuring function and graph divergence is useful and falsifiable once operationalized. The current resource-flow model's new sweep tests ten paired seeds under eight perturbations and reports prediction error and current-source share. Those results show limited sensitivity in that toy stream. The report does not define an acceptable functional deviation or measure graph distance, and the tested predictor repertoire has only three fixed source-edge types. It is therefore not yet evidence that substantially different network structures preserve the same function.

Before using this as a unifying hypothesis, specify one environment and task, a functional output distance and tolerance, the perturbation distribution/range, and a graph-distance or unit/edge divergence metric. Pre-register the expected function-stability range and its falsifier. Include perturbations that remove or disable the proposed buffering interaction; otherwise robustness cannot be attributed to that mechanism. Keep the current result as a sensitivity pilot.

## Opened source

- Biswas, S., Emond, M. R., Philip, G. S., and Jontes, J. D. (2026). “Canalization of neural dynamics by δ-protocadherins in the developing zebrafish optic tectum.” PLOS Genetics 22(6):e1012171. Full text opened through shared/lit.py: https://pmc.ncbi.nlm.nih.gov/articles/PMC13241009/
- The earlier bioRxiv preprint was also opened; a peer-reviewed version is now available, so use the 2026 PLOS Genetics article as the primary source.

Review date: 2026-10-22. No claim of exhaustive prior-art search.
