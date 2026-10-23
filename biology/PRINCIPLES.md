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
