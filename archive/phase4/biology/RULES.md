# Biology Rules

- Stochastic cell identity can preserve heteroneuronal contacts while removing self-contacts in the toy (`0/534.350` self and `1856.934/4481.100` hetero survivors); a single shared identity removed both, and no identity removed neither (500 seeds). This is a mechanism check, not organism evidence; test code collisions and growth cost in organism.
- With 500 seeds and fixed toy paths, pool size and code length traded off heterocontact retention: a 4-ID code retained `0.4181` at 22 isoforms and `0.7477` at 58; in 22 isoforms, 1 ID retained `0.9562` and 8 retained `0.0092`. Self contacts stayed `532.746` because all branches share the cell code. This supports the collision mechanism only; test changing contacts, code cost, and organism outcomes.

- Local memory pools reduce interference in the toy regression only when
  task routing is supplied; test whether routing can emerge without labels.
- Do not treat dendritic branch routing in the toy demo as organism evidence.
- Two-stage pruning toy confirms only the imposed selection and edge-removal
  operations; test protection, timing, and organism outcomes separately.
- Timing-based selection degrades when target coincidence is weakened in the
  toy sweep; its apparent 8/20 boundary depends on the imposed setup.
- The expanded pruning sweep retained both imposed targets through 8/20
  coincidence, fell to 1.0185/2 at 4/20, and none at 0/20 (2000 seeds); this
  is a toy sensitivity boundary, not a biological threshold.
- Local capture gates protect a stable trace better than a global mean gate
  in the two-module toy; threshold and capture values are imposed, so test
  locality in organism before treating it as a design rule.
- In the neurogenesis toy, age-gated newborn units retained the first similar
  context (`1.000`) while learning all eight (`1.000`); no birth (`0.478`,
  `0.500`) and always-broad plastic units (`0.463`, `0.492`) collapsed toward
  chance. The eight-unit cost and all thresholds are imposed; this is not an
  organism result.
- In the assembly replay toy, matched replay reduced prototype MSE to `0.0104`
  and gave `0.7410` probe accuracy; no replay gave `0.3373` and `0.5356`, while
  shuffled replay gave `0.4731` and `0.3512` (500 seeds). Replay must target the
  local trace; this is a forced-prototype result, not an organism result.
- In the adaptive-myelin toy, a local finite budget beat a global equal split
  on adaptation to a changed path (`0.1362` vs `0.3588` MAE, 500 seeds) while
  both outperformed no sheath (`0.8326`); initial accuracy and old-path
  retention were only modestly different. The budget, drift, and path labels
  are imposed, so this is a mechanism check, not organism evidence.
- The matched myelin sweep found a resource boundary: at budget `3.2` and
  drift `0.006`, local/global/new-path MAE was `0.1362/0.3588/0.8323` (300
  seeds), but at budget `6.4` global reached `0.1250` versus local `0.0845`.
  Local allocation is therefore a scarcity hypothesis, not a universal win;
  see `biology/results/adaptive_myelin_sweep.result.txt`.
