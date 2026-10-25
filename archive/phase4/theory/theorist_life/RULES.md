# Rules learned

- A metabolic state can couple retention and exploration: high energy preserves an association, while depletion returns control to current sensory evidence.
- In the organism-v3 protocol, this homeostatic gate reached 2.4023 mean rooms versus 0.0176 for the fixed-fallback parent; the comparison is the current ablation.
- Survival and room reach must be read from `sandbox/leaderboard.jsonl`; short smoke runs are not evidence of advancement.
- Ablation in organism-v3: removing energy-dependent movement (fixed speed 0.575) raised rooms_reached to 2.8408 (survival 0.8887, room 5 fraction 0.0977), while removing energy gating from trace retention/readout lowered it to 2.0313 (survival 0.9434, room 5 fraction 0.0391). The useful mechanism is metabolic sensory trace selection; energy-modulated speed is harmful here.
- In organism-v4, energy-dependent disuse pruning gave 2.3242 rooms versus 2.3076 with the same rule and pruning coefficient zero; maximum live links fell 34.44 versus 35.75, while survival fell 0.9063 versus 0.9229. Resource-conditioned pruning trades survival for a small room gain and smaller structure.
- A cross-over that added signed post-bite energy-loss updates to the sparse scarcity-pruned links scored 2.0391 (survival 0.9346), below the H009 parent at 2.3242. Negative causal updates reduced room progress despite similar maximum links (35.47); H016 is refuted.
