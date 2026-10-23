# Theory state — local evidence-driven structural plasticity

## Scope and status
This is an initial, falsifiable toy hypothesis, not a claim of a complete learning system. The present simulation uses an externally supplied binary stream with an identifiable correlation switch. It does not solve unsupervised goal formation, bounded lifelong memory, or Crafter learning. No external reward or backpropagation is used in the update rule.

## Definitions
Let time be discrete, with source event `x_t ∈ {0,1}` and target events `y_{i,t} ∈ {0,1}`, `i ∈ {1,…,N}`. Each candidate directed edge has nonnegative state `w_{i,t}`. Each endpoint stores exponential traces

`m^x_t = m^x_{t-1} + α(x_t - m^x_{t-1})`,

`m^i_t = m^i_{t-1} + α(y_{i,t} - m^i_{t-1})`.

The simulated local update is

`c_{i,t} = x_t y_{i,t} - m^x_{t-1}m^i_t`,
`w_{i,t+1} = max(0, w_{i,t} + η c_{i,t} - λw_{i,t})`.

An edge is called active at readout iff `w_i ≥ θ`. This uses only current endpoint events and local traces. Note this is an online covariance-like plasticity rule; its finite-sample trace product is not an exactly unbiased covariance estimator.

## Hypothesis H1 — local correlation tracking under a regime switch
If one target becomes correlated with the source while all other target rates remain at chance, then H1 predicts that its edge crosses θ quickly after a switch and unrelated edges eventually decay below θ. The simulation supports rapid target-edge occupancy for one seed but **does not support eventual pruning or reliable identification**: after 6,000 steps, precision remains modest. Treat H1 as falsified in its current strong form (persistent unrelated edges), not as established.

### Evidence (only the recorded run)
`sim/local_plasticity.py`, seed 20261022, N=8, T=12,000, switch at 6,000, η=.008, λ=.0005, α=.02. At θ=.5: post-switch target threshold occupancy after 100 steps = 0.9761; active-edge precision in regime 0 = 1.0 and regime 1 = 0.5881; active-edge fractions = .1209 and .2040. At θ=.1: target occupancy = 1.0, precisions = .4023 and .3545, active-edge fractions = .3094 and .3505. These are single-seed toy results, not uncertainty estimates or Crafter results. Result JSON is written by the script on execution and corresponds to the last executed threshold (.5).

## Falsifiers / next test for H1
H1 is falsified for this update/parameterization if longer stationary runs continue to accumulate unrelated active edges or switch recovery fails under repeated switches. Stronger multi-seed evaluation should report (a) time to target activation, (b) false-edge lifetime / precision, (c) structural edge count, (d) performance against fixed-edge and no-learning baselines, and sweep α, η, λ, θ. A future competitive normalization or explicit local synaptic-competition term is a distinct hypothesis and must be simulated before proposing it as a fix. Test under event-rate shifts separately; this experiment only shifts correlation identity.

## Hypothesis H2 — coactivity-gated probationary sprouting

### Definition
Use a source unit with a local neighborhood of `N` possible postsynaptic partners and a hard limit `K` on total formed contacts. One of those slots is a temporary sprout; the other `K−1` slots hold stabilized contacts. When the source and one or more unconnected neighbors coactivate (`x=y_i=1`), the source samples one coactive neighbor uniformly and forms a temporary contact. Each contact stores only endpoint exponential traces, initialized to the neutral Bernoulli(0.5) state, and estimates `s_i = EMA(x y_i) − EMA(x) EMA(y_i)`. The contact-forming event is excluded from the estimate because it was selected by coactivity. After `P` steps the temporary edge stabilizes if `s_i > θ_g` and a mature slot is empty, or if it exceeds the weakest mature edge; otherwise it is retracted. A mature edge is pruned after its score remains below `θ_p` for `D` consecutive steps. In the tested variant, `K=2` or `3`, `P=50`, `θ_g=.08`, `θ_p=.025`, `D=100`, and EMA rate `.02`.

This defines an explicit, changing edge set: birth is temporary contact formation, stabilization is retention, and death is retraction or pruning. At each update the mechanism uses activity in the local neighborhood and traces at the two endpoints. It has no reward, label, backpropagation, or ranking of the full candidate set by score. It does assume the local neighborhood can reveal which neighbors are currently active and starts its rate traces at `.5`; neither assumption has yet been tested under broader activity statistics.

### Falsifiable prediction
On the balanced eight-regime stream in `sim/probationary_sprouting.py`, the `K=2`, coactive, 50-step variant should maintain target coverage above `.75`, reach 50 consecutive target-containing steps within 250 steps on average, and retain fewer than `.01` stable edges per step on an independent Bernoulli null stream, while never exceeding two total contacts. The idea is falsified in this test family if a multi-seed replication falls to chance-level coverage (`1/N`), misses the recovery bound, exceeds the null-contact bound, or violates the hard capacity.

### Evidence from the recorded execution
Command: `nice -n 15 .venv/bin/python -I theory/theorist_axioms/sim/probationary_sprouting.py`. The deterministic run used 20 seeds, `N=8`, eight regimes of 1,500 steps, and 12,000 steps per seed. For `K=2`, coactive sprouting with 50-step probation, target coverage was `.8806` (across-seed SD `.0316`), mean recovery to 50 consecutive target-containing steps was `179.1` steps, recovery succeeded in all 160 regime windows, and stable-edge precision was `.9053`. Maximum total contacts observed was 2. In the separate independent null stream, 20 seeds produced zero births and zero stable contacts. The fixed random-edge coverage control is `.125`.

The ablation on the same run found uniform-random sprout selection at `K=2`, `P=50` achieved `.7658` target coverage (SD `.0854), mean recovery `338.6` steps, and null stable-edge occupancy `.00153`; it did not meet the prediction. Coactive `P=100` was slower (`.7189` coverage, `414.6` steps mean recovery), so shorter probation was better here. Raising capacity to `K=3` modestly increased coverage to `.8886` and reduced mean recovery to `167.1` steps, but stable-edge precision fell to `.8110`. These are toy stream results only; no evidence yet covers changing event rates, larger neighborhoods, spatial geometry, or useful sensorimotor behavior.

The original simulation supported H2 narrowly. H001 was later independently replicated on its registered stream family and is now `supported` in `shared/hyp.py`; the critic found no exact identical sequence but identified prior art for its constituent families. It does not establish novelty, biological validity, or a general learning mechanism, and it is not the single-principle target below.

## Unification pivot — minimum causal description length

H2 is a useful component test but not the target principle: its fixed probation interval, two evidence thresholds, and reserved sprout slot are separate controls. The new candidate is that the whole learner is a **causal code** for its sensory stream, and every persistent internal distinction must justify its bits by shortening that stream's code.

### Objects and one objective
At time `t`, let `A_t=(G_t, θ_t, m_t)` be the current predictive architecture: a local directed graph `G_t`, local predictive parameters `θ_t`, and their sufficient state `m_t`. Let `z_t` be the current sensory vector. A causal predictor factorizes over local units, so its prequential data code is

`L_data(z_1:T | A_0:T-1) = Σ_t Σ_v -log₂ q_{v,A_{t-1}}(z_{v,t} | z_{Pa(v),t}, m_{v,t-1})`.

Let `L_U(A_0, A_1:T)` be a prefix code for the initial graph and the sequence of local edits (endpoint, edit type, and waiting duration). The one objective is

`L_total = L_data + L_U(A_0, A_1:T)`, subject to `bits(A_t) ≤ B` at every time.

The system's state transition is posterior sampling over admissible local architectures and parameter states, with path probability proportional to `2^(-L_total)`. For a local edit `A→A'`, its posterior odds are the predictive bits saved by the edit minus the bits required to describe that edit. No independent growth threshold, pruning threshold, learning rate, or mutation bonus is part of the rule. A practical local sampler can use a symmetric one-edit proposal and accept it with `min(1, 2^(-ΔL_total))`; its stationary distribution for a fixed data prefix is proportional to the same code posterior.

Growth and pruning are changes in `G`; parameter learning is the update of `q` that shortens the next sensory code; memory is the retained graph and predictive state that allow future code savings; exploration is a posterior draw of a plausible local edit. These are different observables of one codelength process, not separately rewarded subroutines. A physical budget `B` remains a boundary condition, not a tuned threshold.

### Coding facts and limits
For any true distribution `p` and code predictor `q`, expected prequential length is `H(p)+D_KL(p||q)`. Thus, for a fixed code family, shortening expected sensory description is equivalent to reducing predictive divergence. If a structure prior is encoded with prefix lengths `L_U(G)`, then posterior odds obey

`log₂ P(G'|z) / P(G|z) = [L_data(z|G)-L_data(z|G')] - [L_U(G')-L_U(G)]`.

This gives an exact interpretation of structural selection: a connection is favored when its predictive code savings pay its description cost. Kraft's inequality bounds the total prior mass of all structures and edits. The finite-state collision argument above still applies: under fixed `B`, some distinctions between histories must be discarded or approximated. The principle does not guarantee that a local search finds the shortest code, that the code factorization is adequate, or that the posterior tracks a regime shift quickly; these are empirical questions.

### Exact toy operationalization and evidence
`sim/causal_code_filter.py` is a reference filter for one local neighborhood with architecture states `{no edge, edge to channel i}` and a hard one-edge capacity. Each architecture segment uses a Jeffreys Beta-Bernoulli integrated code. Graph size uses the universal prior `p(k)=1/[(k+1)(k+2)]`, conditioned on the physical cap `k≤1`; edge identity is uniform given `k`. A topology change draws from that same prior conditioned on changing state. Segment duration uses `p(d)=1/[d(d+1)]`, so survival is `1/d` and there is no hand-set probe or reconfiguration interval. The posterior over the current architecture is updated from the joint code of sensory data and graph path.

Ran `nice -n 15 .venv/bin/python -I theory/theorist_axioms/sim/causal_code_filter.py`. With `N=4`, 20 seeds, four 300-step regimes, and one edge allowed, the posterior-mode structure tracked the rotating correlated target with mean coverage `.9685` (SD `.0033), mean recovery to 25 consecutive correct-edge steps of `10.16` steps, and success in all regime windows. Mean posterior mass on the current target edge was `.9529`; the mode had `.9766` edge occupancy and made `9.8` structural changes per run. Its prequential code length was `3.1196` bits per step. Fixed random one-edge wiring covers `.25` of this balanced schedule.

On 20 independent Bernoulli null streams, mean posterior mass on any edge was `.1841` (SD `.0340), while the posterior-mode structure contained an edge on `.00758` of steps (SD `.0128); predictive code length was `4.0227` bits per step. The topology never exceeded one edge because the state space imposes that capacity. All numbers are from `sim/causal_code_filter_result.json`.

The seed-0–19 execution is development evidence only. On the registered fresh seeds 20–39, the independent exact replication exceeded the null MAP-edge occupancy bound: `.0492 ± .1612` against `<.02`, with seed 38 at `.72`. Its target coverage, recovery, and codelength bounds passed, but the registered hypothesis required every bound to pass, so H002 is **refuted**. See `experiments/h002-reference-replication/result.json` and the critic's audit. The one-edge cap is imposed by the enumerated state space; the filter stores history-dependent path evidence, evaluates alternatives while absent, and reports a mode rather than a sampled physical graph. It therefore does not establish emergent growth, bounded online memory, useful exploration, or recall after a returning regime. No claim of novelty or broad intelligence is made.

## Resource / mathematical boundary
A finite-state machine with a fixed number of states cannot encode an unbounded amount of mutually distinguishable past information: by the pigeonhole principle, two distinct histories map to the same state, so any future query distinguishing those histories cannot be answered correctly for both. This does not rule out indefinite learning of a restricted/stationary task family, approximate compression, or physical systems with unbounded external storage. It makes the resource assumptions explicit: an indefinitely learning agent under bounded resources must discard information, compress it, or accept nonzero errors; “never forget anything” is not a viable universal requirement.

## Action identifiability boundary

Let two worlds induce the same distribution over every observation available before intervention, but let their action-outcome maps be reversed so their optimal actions differ. Any policy whose state is a function only of passive history has the same state distribution in both worlds, and therefore the same action distribution. It cannot choose the opposite optimum in both. This is an identifiability result, not a learning-rate limitation: more passive data cannot recover a distinction absent from the observation law.

The executable witness `sim/action_identifiability.py` generated 40 paired worlds with 1,000 observations per world. The re-run recorded identical passive histories in all 40 pairs, mean passive difference `0.0`, and opposite best actions in all 40 pairs (`sim/action_identifiability_result.json`). Consequently, deriving useful action choice requires both evidence conditioned on interventions and an ordering of their consequences. Neither follows from passive predictive accuracy alone. The ordering is an additional boundary condition on any self-building principle; declaring persistence or prediction to be intrinsically valuable would add that preference rather than derive it.
