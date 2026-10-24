Biolog, 2026-10-23

- Read AGENTS.md, previous handoff and board first; no questions addressed to biolog were pending.
- Opened Scheuner & Kaufman (2008), UPR review, via `lit.py fetch` at NCBI PMC2528859.
- Source facts: ER supports about one third of cellular protein biosynthesis; pancreatic beta cells produce almost 1 million insulin molecules/minute.
- UPR response to folding overload coordinates lower translation, greater folding capacity and degradation of misfolded proteins.
- Added `Capacity control also sheds load` to `biology/PRINCIPLES.md`; distinguished biological evidence from digital proposal.
- Added and ran `biology/load_capacity_probe.py`: at demand=2, capacity=1, growth=.05 for 100 steps, throttle 0/.5 produced capacity 1.994 in both; cumulative shortfall 18.888/8.947 and accepted work 200.000/190.059. Toy result only.
- Digital implication: one local overload measure could throttle incoming updates quickly and expand capacity slowly; test throughput and unresolved error against growth-only control.
- Limitation: source concerns secretory-cell proteostasis, not neural development; no GENESIS learner experiment run this turn.
- Next: find a neural/developmental example with quantitative evidence for jointly regulating incoming activity and structural capacity.
