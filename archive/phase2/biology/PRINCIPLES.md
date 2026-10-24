# Biology-derived principles

## Vacancy keeps a losing connection revisable

At developing mouse neuromuscular junctions, multiple motor axons initially share
postsynaptic sites and usually resolve to single innervation. Turney and Lichtman
removed one input with laser ablation at 15 junctions (P7-P8 mice). In every case
the remaining input expanded; in 14/15 it occupied the whole junction within 24 h,
including cases where it started with only 1-5% of the territory. The growth also
occurred at sites on functionally innervated muscle, so global target inactivity was
not required. (Turney & Lichtman, 2012, PLoS Biology 10:e1001352,
doi:10.1371/journal.pbio.1001352; full text opened with `shared/lit.py fetch`,
Europe PMC PMC3383738.)

**Principle:** until local access is lost, apparent losers remain revisable. A
vacated contact site is an opportunity for a neighbor to expand into; pruning and
growth can therefore be two sides of local competition for finite sites, rather
than an irreversible loser label followed by independent regrowth. The paper
supports local, reversible competition but does not establish its molecular cause.

**Digital implication:** represent capacity as local addressable sites. Units that
retain a foothold can claim newly vacant nearby sites; a unit with no sites can be
removed. A perturbation that removes a dominant unit should release capacity to a
weak neighbor, without a global reward or target-wide inactivity signal. Treat this
as a testable design hint, not a demonstrated learning law. The toy model in
`vacancy_competition.py` checks only the occupancy consequence.

## Slow structural change can absorb what fast regulation cannot

Aljaberi, O'Leary & Forni model homeostatic synaptic scaling together with slow
activity-dependent structural growth. Their model's equilibrium condition bounds
average channel capacity by morphology (`g_avg <= c sum(s_i)/(n omega_g)`), so a
target activity of 0.5 is unreachable from initial `L0=0.1` without growth in their
illustrated simulation; with growth, activity asymptotically reaches 0.5 as length
increases. They also simulate aggressive fast feedback (`k_u=0.01`, `L0=0.25`):
fast scaling alone oscillates pathologically, while adding slow growth damps the
oscillations and reaches the target. Their parameters use two compartments (`n=2`)
and structural adaptation timescale `tau=10^5`; the paper reports that reducing
timescale separation makes stability more fragile. These are results from a
system-theoretic model, not measurements of those exact values in animals.
(Aljaberi, O'Leary & Forni, 2020/2021, "Dendritic trafficking: synaptic scaling and
structural plasticity," arXiv:2011.12067, DOI 10.48550/arXiv.2011.12067; full text
opened with `shared/lit.py fetch https://arxiv.org/html/2011.12067`.)

**Principle:** a fast variable can regulate current activity only within existing
capacity; a slow structural variable can change the feasible range. Driving the
slow variable from a filtered/persistent activity bias lets it absorb sustained
error and can damp fast oscillatory correction. Do not treat fast and slow changes
as duplicate learning rates: they control different constraints.

**Digital implication:** separate edge weight or activation from a slower local
capacity/topology variable. Let capacity change only under persistent signed error,
with a slower update than fast weight adaptation. Test whether this prevents
oscillation and removes capacity-imposed error without adding reward. The cited
paper provides a model precedent; its effect in a digital learner remains untested.

**Stability qualification:** this is not a claim that adding any slow growth rule
stabilizes feedback. Under the paper's assumptions, Theorem IV.1 gives a maximum
fast feedback gain and minimum growth time constant for global exponential
stability. Its simulations show increasing fragility as `tau` falls through
`10^4`, `10^3`, and `10^2`; at sufficiently small `tau` oscillations persist.
For `n=2`, the parameter set uses `tau=10^5`. This makes timescale separation a
condition to test, not a decorative second learning rate.

**Digital implication:** sweep the ratio of structural to fast adaptation time,
including values on both sides of the stable regime, and report oscillation
amplitude as well as mean error. `structural_capacity_probe.py` only checks the
capacity feasibility bound and its simple slow relaxation; it does not reproduce
the paper's trafficking model or establish oscillation damping in a digital
learner.

## Capacity control also sheds load

The unfolded protein response (UPR) couples three responses to excess protein-
folding load in the endoplasmic reticulum (ER): it attenuates new translation,
increases folding capacity, and increases degradation of misfolded proteins.
The ER handles about one third of eukaryotic cellular protein biosynthesis;
pancreatic beta cells can produce almost one million insulin molecules per
minute. These values indicate that the load-control problem is large even in a
single specialized cell. The source is a review of cellular UPR mechanisms,
not evidence about neural development or a single universal controller
(Scheuner & Kaufman, 2008, *Endocrine Reviews* 29:317-333,
doi:10.1210/er.2007-0039; full text opened via `shared/lit.py fetch`
`https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2528859/`).

**Principle:** when processing demand exceeds capacity, biology can reduce the
incoming load while also increasing capacity, and clear failed products. The
short-term response need not wait for the slow structural response; the two
act on different sides of the same load-capacity mismatch.

**Digital implication:** derive one local overload signal from work demanded
versus available processing capacity. Let it promptly limit new updates or
growth proposals, while persistent overload slowly increases capacity; remove
representations that repeatedly fail local consistency checks. Test the
combined rule against capacity growth alone, measuring both unresolved error
and throughput. This is a translation proposal, not a tested GENESIS result.
`load_capacity_probe.py` compares load shedding with capacity growth alone in a
deterministic toy model; it exposes the throughput cost but is not biological or
learner validation.
