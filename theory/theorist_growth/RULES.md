# Rules

- Structural growth is not evidence of useful growth: `growth_trace_island` and its static-structure ablation had identical full v6 scores and survival.
- A fixed dense tensor with thresholded nonzero entries measures active structure, not memory savings; report allocated state separately.
- `growth_local_eligibility` scored identically at limits 302, 1000, 10000, and 100000; capacity alone did not cause scaling.
- Do not confirm or discard a growth mechanism from one seed or a shortened life; compare against an ablation across seeds and scales.
- In `metabolic_sparse_probe.result.json`, initial state stayed at 476 B across limits 302 to 100000; 80 synthetic active steps raised it to 1052 B, and 1000 quiet steps returned it to 476 B with zero keys. A capacity limit alone does not allocate state, and this structural effect does not establish predictive or behavioral value.
- The corrected per-organism sparse candidate reached the same full-v7 score as its parent (`0.0068359375`) across 302/1000/10000/100000 limits; metabolic reserve weighting changed structure but did not show a behavioral gain in the one-seed run.
