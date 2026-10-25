# agency_trace

`candidates/agency_trace/principle_organism.py` implements a batched action loop.
It estimates a bearing from the eye, explores when no signal is visible, and
updates a per-organism channel preference after an endogenous energy increase.

The judge run at 302 units scored 0.068359375 with mean `rooms_reached=0.068359375`.
The matched `trace=False` ablation scored 0.0625 (`+0.005859375`), below the
pre-registered +0.05 criterion, so the claimed causal effect is refuted.
