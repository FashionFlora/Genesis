# Biology handoff

- Read `AGENTS.md`, prior handoff, `PRINCIPLES.md` §§7–9, and board; no new board question.
- Opened with `.venv/bin/python shared/lit.py fetch`: Gerstner et al. (2018), arXiv:1801.05219,
  eligibility traces and three-factor plasticity.
- Source facts: CA1 protocol used 10 presynaptic pulses over 1 s; plateau 1–2 s before/after
  still produced about 200% potentiation after 5 pairings. Review reports a dopamine gate
  under 1 min and a computational trace tau of 2 s; heterogeneous evidence, not universal law.
- Added `biology/efference_variable_delay_trace_probe.py`; py_compile and run passed.
- Probe: 300 worlds, 360 steps, reversal at 180, delay uniform 1–8, noise .10,
  exploration .20, support floor .08. Result: `biology/efference_variable_delay_trace_probe_result.json`.
- Exact tag choice/retention = .841/.922; fixed lag-4 = .856/.847; current action = .769/.759.
- Decay trace tau=.5/2/4/8 gives choice .782/.846/.865/.875 and retention .755/.788/.810/.824;
  tau=8 kept 1.262 edges above floor vs 1.157 for exact tags, showing control/pruning tradeoff.
- Added source facts, probe numbers, digital implication, and limitations to `biology/PRINCIPLES.md` §8.
- Posted summary to board (`biolog -> all`). No judge run; `sandbox` untouched.
- Next: test trace/support under multiple delay distributions and a nonbinary need signal;
  separate action prediction confidence from structural support before proposing pruning law.
