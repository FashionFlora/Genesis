# Metabolic eligibility

The working principle is that a living controller treats an energy change as a
local eligibility signal. The colour pursued immediately before the change is
credited, with a short decaying trace. A second, low dimensional visual context
keeps traces from incompatible regimes separate. The reserve also gates urgency
and search, so depletion changes how the organism spends motion.

The principle is distinct from the current RGB controller details. The
alternating retinal sectors, thresholds, five-step bite pulse, phase sweep, and
fixed three-colour palette are implementation choices that need permutation and
ablation tests. The full v6 result supports the combined trace-plus-context
mechanism, not each detail separately.

Evidence: `candidates/life_metabolic_context/principle_organism.py` scored
0.76171875 rooms reached (CI 0.7074239401..0.8160135599) in 1024 worlds;
learning-disabled matched ablation scored 0.0634765625 (CI
0.0464692664..0.0804838586). No interoception scored 0.0625 (CI
0.0458054363..0.0791945637). Parameter perturbations exposed poor robustness.
