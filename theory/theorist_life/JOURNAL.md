# Journal: odkrywca_life

## 2026-10-25: shared metabolic budget mutation

Created `candidates/life_metabolic_shared_budget/principle_organism.py` from
`life_metabolic_competition` and `life_metabolic_ratio`. The only behavioral
change is a single zero-sum projection over all six color/context memories,
testing whether finite metabolic memory is shared across contexts. `ideas.py
check` was NEW (maximum similarity 0.09); syntax compilation passed. Full v7
was launched for 1024 worlds, 50,000 steps, n_units=302 as PID 507064 (session
37259). After about 107 minutes it was still running; all six GPU slots were
often occupied by other organism-v7 assays. No leaderboard row or score exists
yet, so this is execution status only, not evidence. A matched learning_rate=0
ablation remains required after the nominal run completes.

## 2026-10-24: competitive metabolic memory

Created `candidates/life_metabolic_competition` as a cross-island mutation of
`life_metabolic_context` and `dynamics_energy_trace`. The change projects each
context's three color preferences to zero mean after metabolic credit, making
colors compete for finite memory. `shared/ideas.py check` was NEW (0.11).
Created matched `life_metabolic_competition_ablation` with learning_rate=0.
Full v7 was launched for 1024 worlds, sizes=[302], but was still running after
90 minutes with no saved candidate row; no causal conclusion is valid yet.

## 2026-10-24

Built `candidates/life_metabolic_context`: an energy-change eligibility trace stores a
colour preference separately for two retinal contexts. The current energy level gates
credit, urgency, and visual search. This keeps metabolism as the local teaching signal;
there is no world reward channel or cross-organism state.

Full organism-v6, 1024 worlds, 12000 steps, n_units=302: rooms_reached 0.76171875
(CI 0.7074239401..0.8160135599), survival 0.7392578125. Matched learning ablation
(learning_rate=0): rooms_reached 0.0634765625 (CI 0.0464692664..0.0804838586),
survival 0.896484375. Difference +0.6982421875; the CI intervals are disjoint.
The effect is therefore tied to the metabolic trace, while it trades off survival.

Parameter robustness was poor: judge variants at factors 0.7 and 1.4 scored
0.064453125 and 0.0615234375. Keep this as a real limitation and test a simpler
parameter-free or normalized trace next. The no-interoception full assay was started
after the matched ablation. It completed at rooms_reached 0.0625 (CI
0.0458054363..0.0791945637), survival 0.890625; factor 0.7 scored 0.0625 and
factor 1.4 scored 0.298828125. Energy sensing is necessary for the effect, and
the current learning scale is not robust. Next test should normalize the trace.

## 2026-10-24: ratio memory mutation

Created `candidates/life_metabolic_ratio`, replacing the learning-rate preference
update with decayed signed energy evidence divided by decayed eligibility mass.
`shared/ideas.py check` reported NEW (maximum similarity 0.10). Full organism-v7
at 1024 worlds and 50000 steps scored rooms_reached 0.0732421875 (95% CI
0.0555342209..0.0909501541), survival 0.86328125; the run took 3573.9 s and was
not disqualified. Parameter factor 0.7 scored 0.072265625; factor 1.4 scored
0.271484375. The nominal result is far below the 0.8 island leader. This is not
causal evidence because no matched ablation of this mutation has run; the next
test must compare it to the same controller with metabolic evidence disabled.

## 2026-10-24: context-free metabolic prototype

Created `theory/theorist_life/metabolic_color_ratio/principle_organism.py`, a
single three-colour signed energy-evidence trace. It removes the retinal
odd/even `room_context` decoder and updates the previous colour using energy
delta divided by eligibility mass. A matched `metabolic_color_ratio_ablation`
sets `metabolic_credit=0` while retaining the same controller.

The CLI wrapper still fails with the known v7 `social_group_size` argument
TypeError, so I called `sandbox/organism_judge_v7.judge` directly. The run was
started with 1024 worlds, 50,000 steps, CUDA, sizes=[302], but waited for a
GPU slot for 52 minutes because other assay processes occupied all slots. It
was interrupted before any result was produced; no score or causal conclusion
exists. `nvidia-smi` showed 100% utilization and about 20 GiB used.

## 2026-10-24: competitive memory stability smoke

The previous full organism-v7 attempt for `life_metabolic_competition` left no
report or leaderboard row, and no process for that assay remains. Four other
organism judge processes were active with GPU utilization at 99% and 22324 MiB
used, so I did not add another full assay. A CPU controller smoke (5000 steps,
32 instances, variable RGB and energy inputs) produced finite actions and
preferences; maximum absolute preference was 1.238154 and the maximum absolute
per-context color-sum was 6e-08. This confirms the projection invariant and
numeric stability only; it gives no evidence about organism performance or
causality. Full v7 candidate and matched-ablation runs remain required.

## 2026-10-25: adaptive shared metabolic budget

Updated `candidates/life_metabolic_shared_budget/principle_organism.py` so
energy credit is divided by each organism's decaying recent absolute energy
change before the six color/context memories compete for one zero-sum budget.
A 5000-step CPU smoke initially exposed runaway preferences (max 132.8); an
explicit [-2, 2] budget bound fixed this (finite actions, max preference 2.0,
mean absolute preference 1.099). `ideas.py check` remained NEW (max similarity
0.09), and py_compile passed. A matched
`life_metabolic_shared_budget_ablation` was created with `learning_rate=0`.
Full v7 nominal run was launched as PID 1111975 (session 77002) for 1024
worlds, organism-seeds=1, author `odkrywca_life`; at handoff it was still
running with no leaderboard row. No performance or causal conclusion is valid
until nominal and ablation records both exist.

## 2026-10-25: adaptive metabolic normalization x reserve retention

Created `candidates/life_metabolic_adaptive_retention_budget` as a three-parent
crossover: retain contextual endogenous-energy memory from `life_metabolic_context`,
reserve-shaped eligibility retention from `dynamics_metabolic_retention`, and
finite shared norm from `axiom_metabolic_context_budget`; add a decaying estimate
of each body's absolute energy-change scale to normalize its signed write signal.
This changes the mechanism rather than just its parameter. `shared/ideas.py check`
reported NEW (max similarity 0.14). The matched ablation forces learning_rate=0.
Both compile; 3000-step CPU smoke at batch 32 produced finite actions (max abs
action 1.0), with activity 0.3226 nominal and 0.0 in ablation. This is numeric
stability only, not organism evidence.

Full v7 nominal judge started for 1024 worlds with PID 1398152/session 37386.
At handoff it had run >63 minutes, was still active, and had produced neither a
leaderboard nor disqualification row. Do not infer a score or effect. Resume by
waiting for this run, then execute the matched full ablation and compare
rooms_reached confidence intervals before judging the mechanism.

## 2026-10-25: adaptive retention full causal assay

The prior nominal process had no record, so I reran the v7 judge directly through
`sandbox/organism_judge_v7.py` and appended the result to
`sandbox/leaderboard.jsonl`. With 1024 worlds, 50,000 steps, and n_units=302,
`life_metabolic_adaptive_retention_budget` reached rooms `0.287109375`, 95% CI
`[0.252028, 0.322190]`, survival `0.8125` CI `[0.788582, 0.836418]`. Its
parameter perturbations scored 0.302734 (factor 0.7) and 0.071289 (factor 1.4).

The matched `learning_rate=0` ablation, same full v7 assay, reached rooms
`0.076171875`, CI `[0.058407, 0.093937]`, survival `0.853516`; both factor
0.7 and 1.4 scored 0.076172. The room difference is `+0.2109375` and the CI
intervals are disjoint, so endogenous metabolic writing has a causal effect
under this judge and the direction is not abandoned. It does not challenge the
0.8 island leader, and the factor-1.4 collapse plus audit capacity RMSE 0.0
show that adaptive normalization is not robust or genuinely using n_units.
The next test should simplify the write/retention rule and isolate normalization
with a matched fixed-scale control before any claim of a deeper principle.

Post-assay critic audit (`audit/adaptive_ablation_critic.result.json`) narrows
the claim: on protocol-aligned constant energy 0.95, nominal and learning-zero
actions are identical; the large action difference appears only after an actual
0.95 -> 0.50 energy step (post-step RMSE 0.9137). Thus the full pair establishes
that metabolic writing matters after reserve changes, but does not isolate the
adaptive delta-scale normalization from inherited context, retention, or the
fixed retinal/timer heuristics. Next matched control must keep learning active
while replacing adaptive scale with a fixed scale.

## 2026-10-25: fixed-scale metabolic control

Created `candidates/life_metabolic_fixed_scale_budget/` from
`life_metabolic_adaptive_retention_budget`. The mutation removes the online
delta-scale estimate and divides clipped energy change by fixed `0.05`; it
retains the same contextual eligibility, reserve-shaped retention, credit
modulation, shared norm budget and action policy. `PARENTS.txt` records ancestry
and rationale. `shared/ideas.py check` marked the mechanism new (maximum
similarity 0.12).

Full organism-v7 judge, author `odkrywca_life`, 1024 worlds x 50,000 steps,
n_units=302: rooms `0.3828125`, CI95 `[0.344420, 0.421205]`, survival
`0.771484`; reached only temporal comparison. Runtime was 3996.86 seconds.
PARAMS factor 0.7 scored rooms `0.319336`, CI95 `[0.282771, 0.355901]`,
survival `0.809570`; factor 1.4 scored `0.487305`, CI95 `[0.446870, 0.527739]`,
survival `0.715820`. The score is above the prior adaptive result `0.287109`
(CI `[0.252028, 0.322190]`, survival `0.812500`), but the fixed-scale version
trades off survival and its perturbations are inconsistent. This is evidence
against an obvious adaptive-normalization advantage, not a paired causal result:
the next assay must calculate same-seed per-world differences in rooms and
survival. The result does not approach the 0.8 leader. Only 302 units were
evaluated; structure remained 3 units, so capacity scaling remains untested.

## 2026-10-25: paired adaptive-vs-fixed scale analysis

The two full-v7 result records retained 1,024 per-world samples each. Both
use the same judge world seed (7) and their per-sample world-family IDs match.
The candidates differ only in metabolic-delta normalization: fixed 0.05 versus
a decaying estimate of recent absolute delta. Paired fixed-minus-adaptive
`rooms_reached` is +0.095703, 95% CI [+0.052685, +0.138721]; survival is
-0.041016, CI [-0.069308, -0.012723]. See
`metabolic_scale_paired_assay.md` for method and scope.

This result points against adaptive normalization in this setting, and the
room gain is bought with lower survival. The adaptation hypothesis is not
parked as a general null: the evidence instead motivates testing how organisms
allocate metabolic memory versus survival under scarce resources. The two
candidate judges are full runs, but the comparison is one paired batch of lives;
it does not establish robustness across independent judge seeds or PARAMS.
