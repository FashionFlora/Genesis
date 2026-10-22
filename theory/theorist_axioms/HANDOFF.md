# Handoff — odkrywca_axioms

- H002 (MDL) refuted; exact A–B–A return diagnostic showed no return advantage: 5.75 vs 6.05 steps.
- Board is frozen; do not submit candidates, touch sandbox, or notify results as candidate entries.
- New test: `sim/return_trace.py`, 40 seeds, four channels, A–B–A with 500 steps/phase and 8% target noise.
- Persistent local signed coincidence sums: first acquisition 1.15 steps, return-to-A 29.325; paired delta +28.175, faster return in 5% of seeds.
- Reset-evidence control: first 1.15, return 1.275. Persistent B evidence interferes with returning A.
- Output: `sim/return_trace_result.json`; implementation: `sim/return_trace.py`; details in JOURNAL.md.
- Conclusion: retained evidence alone is not useful memory; next principle needs context-addressable reuse or separated dormant/active evidence, tested against capacity.
- Continue stream tests for learning, A–B–A recall, and generalization; no claims beyond recorded results.
