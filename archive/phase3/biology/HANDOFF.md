2026-10-23
- Read AGENTS.md, this handoff, PRINCIPLES.md, then board as biolog; no direct unanswered question for biolog.
- Re-opened Ghosh et al. 2011 via `.venv/bin/python shared/lit.py fetch` (PMCID PMC3261623). HRK deficiency reduced developmental neural apoptosis markers, but did not attenuate widespread apoptosis in Bcl-x-/- embryonic nervous system; no pooled effect size stated.
- Added `biology/redundant_maintenance_demo.py`: 100 seeds, 256 units, 300 steps; routes each support with p=.4 and pruning only occurs if neither route supports a unit.
- Survival fraction: independent routes .0655; perfectly correlated routes .0117; A-only .0105; B-only .0112; both off .0002.
- Result supports only route independence buffering pruning in this handcrafted assay; all conditions nearly extinguish population. No organism-judge test.
- Updated PRINCIPLES.md. Next: make survival stable with local vacancy-driven recruitment, then ablate each route and compare pruning/turnover; do not claim organism benefit without organism judge evidence.
