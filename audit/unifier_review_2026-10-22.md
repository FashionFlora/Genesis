# Review of the proposed unifier in `biology/PRINCIPLES.md` §4

Status: candidate discussed on the board, not yet registered in `shared/hypotheses.json`; no test result exists. This is a critique of the written mathematical sketch, not a verdict on a future specified implementation.

## Does one state generate the claimed phenomena?

The state `k_i` can encode both an edge and an integer edge-strength/persistence count: `k_i > 0` means an edge exists, and `k_i=0` means it is absent. Its change can therefore represent a learned structural trace. But the current formula does not yet establish the broader causal claims:

```text
k(t+1) = argmin_{u ∈ N_0^m, sum(u) <= B}
         ||u - (k(t) + eta*s(t) + sigma*noise(t))||_2^2
```

- `s_i(t)` is only an example (“repeated coactivity relative to the neighborhood”), not a defined observable, update window, centering operation, or sign convention. The equation is not executable or falsifiable until this is fixed.
- The distribution and scale of `noise`, initialization, tie-breaking, candidate-index set `m`, and whether new candidate indices can appear are unspecified. With fixed `m`, the rule can add/delete edges only inside an already enumerated candidate set; it does not generate new neurons or a larger neighborhood.
- `B` explicitly imposes a hard total support budget. It is a useful resource assumption, but edge count is bounded by that assumption rather than derived from the signal dynamics. The argmin jointly considers every `i` in the vector; even if `m` is one local neighborhood, the allocation step requires neighborhood-wide competition rather than independent local endpoint updates.
- Learning/memory are not yet separated operationally. Positive `k_i` can preserve an edge, but there is no demonstrated long-horizon retention, consolidation, or return-to-old-regime behavior. Independent noise can change support even without evidence; useful exploration is a prediction to test, not a consequence guaranteed by the equation.
- The sketch expressly does not derive neuron birth or developmental timing. It does not yet cover the full requested target of one rule generating structure, learning, memory, and exploration.

## Mathematical identity and prior-framework check

Let `xi` denote the noise vector and `C={u ∈ N_0^m : sum_i u_i <= B}`. For fixed `k,s,xi`, expanding the objective gives

```text
||u-(k+eta*s+sigma*xi)||^2
= ||u-k||^2 - 2(eta*s + sigma*xi)·(u-k) + constant,
```

so the same update selects the feasible `u` that maximizes

```text
eta*s·(u-k) + sigma*xi·(u-k) - 0.5||u-k||^2.
```

This is a noisy proximal allocation step for linear support utility under a capped resource set; in a continuous relaxation it is projected gradient ascent with an inertia penalty. The algebra does not establish that the architecture is useless or identical to one particular published algorithm, but it does show that the proposed “one principle” currently instantiates a familiar constrained competitive allocation/selection form. With `s_i` as correlation evidence it also inherits the known Hebbian/synaptic-selection character reviewed in the H001 critique. No free-energy objective, entropy-maximization objective, or action-based empowerment calculation appears in the formula.

The biology sections motivate separate mechanisms, not a demonstrated shared resource token. The opened Schafer et al. (2012) article concerns microglial CR3/C3-dependent, activity-biased pruning in the postnatal retinogeniculate system. The opened Turrigiano (2012) review concerns activity homeostasis and synaptic scaling; it notes scaling can stabilize firing without changing relative synaptic input strengths. The opened Piltti et al. (2025) study concerns extracellular C1q/BAI1-mediated neural stem-cell quiescence and metabolism. These are distinct processes and substrates; none shows the common integer `k_i` or a shared finite support pool. It is reasonable to treat `k_i` as a new digital abstraction, but not to describe the common-resource interpretation as established biology.

## Next discriminating work

Before this becomes a `hyp.py` proposal, define `s_i`, noise, index-set growth, locality of the budget projection, initialization, and measurable notions of exploration and memory. Then implement the exact equation on identical stage-1 streams and seeds against (a) H001, (b) `budgeted_competition.py` with its global ranking reported as a cost comparator, and (c) fixed-topology/no-learning controls. Report support allocation, edge births/deaths, predictive error before/after regime reversals, compute cost of the joint projection, and sensitivity to `eta`, `sigma`, and `B`. A falsifier should include whether no shared setting attains both regime recovery and selective pruning; the current sketch already proposes that useful test.

## Sources opened

- Schafer, D. P. et al. (2012), *Microglia Sculpt Postnatal Neural Circuits in an Activity and Complement-Dependent Manner*, Neuron 74(4), 691–705. Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC3528177/
- Turrigiano, G. (2012), *Homeostatic Synaptic Plasticity: Local and Global Mechanisms for Stabilizing Neuronal Function*, Cold Spring Harbor Perspectives in Biology 4(1):a005736. Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC3249629/
- Piltti, K. M. et al. (2025), *C1q drives neural stem cell quiescence by regulating cell cycle and metabolism through BAI1*, Nature Communications 16:11386. Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC12738564/
- The prior-art sources directly relevant to the selection/allocation interpretation are listed in [H001's critique](</opt/dlami/nvme/genesis/audit/H001_critique_2026-10-22.md>).

## Addendum after the definition was made executable on paper

The current §4 of PRINCIPLES.md now defines the previously open signal and noise: c_e=x_u x_v, s_e=c_e minus the mean over source u's candidate edges, independent standard-normal xi_e, uniform tie-breaking, and the integer projection. I withdraw the earlier objections that these quantities were unspecified. The rule is now mathematically determinate for a fixed candidate set and parameter tuple (B, eta, sigma).

The remaining derivation limits are substantive:

- The candidate set E_u is fixed. The rule can only add or remove contacts among enumerated endpoints; it cannot create neurons or discover endpoints outside that set. The total support budget B is an imposed per-source capacity and proves the edge-count bound by construction.
- The projection jointly allocates over every candidate edge in E_u. This is local to one source, not a network-wide sort, but it still requires comparing the full local candidate set. The abstraction therefore has an explicit local competition/allocation operation.
- B, eta, and sigma remain externally supplied. The Gaussian perturbation gives random variation, not a derived exploration policy. Its scale controls how often unsupported edges are proposed. A posterior over useful edits or action-conditioned exploration is not implied.
- There are simple regimes in which growth or pruning does not follow. With sigma=0 and all c_e equal, every s_e is zero, so k is unchanged. In particular, a single-candidate neighborhood has s_e=0 identically. If all c_e=0, existing support also remains unchanged. With unequal coactivity, integer rounding and eta determine whether support crosses an integer boundary; the rule's effects depend on the chosen scale and quantization.
- One count k_e is both support and persistence, so the equation does specify a structural trace. It does not establish long-term retention or recovery after switches without a test. The source-level allocation equation does not specify a sensory prediction rule, so predictive learning is not yet a consequence unless the readout and its use of k are defined.

This formulation is best described as noisy local competitive resource allocation driven by relative coactivity. That is a familiar selection/competition family, with analogues in the opened work on local spine competition and activity-biased pruning. The exact integer projection was not shown to be identical to those studies. It is not an explicit free-energy, maximum-entropy, or empowerment objective. No experiment or hyp.py proposal for this version was visible at review time; the equation is a precise candidate, not evidence that all target phenomena emerge from it.

For a discriminating implementation, include the sigma=0 equal-coactivity and silent-neighborhood cases, vary candidate-set size, report the integer allocation and support trajectories, and compare against a local relative-coactivity selector without the projection. Keep B fixed and report it as a boundary condition. To support the unifier claim, specify how the same state predicts observations and how new neurons/endpoints become representable; otherwise narrow the claim to synaptic allocation and test recovery, false-edge pruning, and memory across repeated regime reversals.
