# Growth rules from runs

- `growth_metabolic_graph` organism-v3 reached score 0.046875 and grew to about 492 reported units; its short instrumentation showed that removing pruning increased persistent units (229 vs 106 at step 1500), but did not test score causality.
- `growth_signed_trace` organism-v4 achieved score 2.3076171875, survival 0.92285, mean energy 0.79012, and reversal latency 247.16. Its first run reported summed units across the 128-member batch, so its growth/limit fields are invalid; rerun with per-organism structure counts before drawing conclusions about scaling.
- A short 64-step smoke test cannot measure learned retention or pruning: initial exposure activates structures immediately, and the window is shorter than the full reversal/foraging task.
