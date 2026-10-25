# Rules learned

- A trace updated by signed energy change can turn a reversal into a local
  relaxation event rather than requiring global relearning.
- In organism-v3, `metabolic_relaxation` reached 0.61914 rooms (8 x 128
  worlds), with 0.86523 survival and 793.38 mean reversal latency.
- The positive-only `energy_association` reference reached 0.01758 rooms and
  5321.73 mean reversal latency in its recorded calibration.
- These are separate calibration runs; an ablation with the signed term
  removed is still required before attributing the gain to negative credit.
## 2026-10-24

- A full organism score is insufficient to attribute a local trace mechanism: same-world controls are required.
- `metabolic_relaxation` with signed energy trace scored 0.9062 rooms in a 128-world, 6000-step run, while the no-interoception version scored 2.2891; the proposed trace effect is therefore not causal.
- The stronger family control was `metabolic_gate` (2.6719 rooms); its energy-gated speed/exploration, rather than negative trace credit, is the plausible source of improvement.
- `metabolic_action_tag` (signed energy trace plus recalled turn vector, fixed speed) reached 1.14453125 rooms, 0.556640625 survival, and 703.5078125 reversal latency in the 8-seed organism judge. The action tag improved over `metabolic_relaxation`'s 0.61914 calibration but did not approach the 2.84082 leader and reduced survival; no causal advantage is established.
- `metabolic_dual_homeostat` adds a separate cost trace after energy loss during a bite. In a short, same-seed 8-world run (2048 steps), both it and `metabolic_gate_fixed_speed` reached 0 rooms; reversal latency was worse (127.375 vs 99.375) and final energy lower (0.9772 vs 0.9897). Room progress cannot be inferred from this horizon, so this is a negative preliminary result, not a full organism refutation; recorded in `dual_homeostat_short.json`. Opened Chalmers et al. (2024), PMC11576168: simulated synapse loss in reward-trained DRL is related prior art, but does not establish this reward-free mechanism.
- `damped_steering_homeostat` adds first-order relaxation of turn output to `axiom_causal_homeostasis`. Matched 8-seed judge (1024 worlds, 6000 steps): rooms fell from 2.8516 to 2.7588 while survival rose from 0.8584 to 0.8760; reversal latency was 118.15 vs 119.50. The inertia tradeoff did not improve the main rooms metric; H012 refuted. Both rows are in `sandbox/leaderboard.jsonl`.
