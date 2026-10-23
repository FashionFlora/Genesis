# Dynamics as computation (orchestrator note, 2026-10-23, from user-supplied lecture transcripts)
Just one example of how ONE system (the human brain) may do it. Not a target, not a checklist, not a direction.
Do not narrow your search to it: a better principle that looks nothing like a brain is welcome.
1. Reservoir computing (Jaeger 2001 ESN, Maass 2002 LSM). A fixed random recurrent network driven by input gives a
   rich *basis* of temporal shapes (Fourier-like argument); only a linear readout is learned, and that is a local,
   non-backprop problem (least squares / RLS / FORCE, Sussillo & Abbott 2009). Echo-state property: every input leaves a
   fading trace; too strong coupling = chaos, too weak = no memory (edge of chaos / criticality).
   Open question for Genesis: can the reservoir *grow and prune itself* by a local law instead of staying random?
2. Memory as the echo term. h_t = W·σ(input) + M(h_{t-1}, x_t). Vanilla copy of the feedforward path forgets; constant
   leak alpha = leaky integrator (membrane); per-unit, context-dependent retention f_t = gated RNN. Question: can
   selective forgetting follow from one quantity (e.g. prediction error, resource) instead of a learned gate?
3. Motor cortex as a dynamical system (Churchland, Shenoy, Kaufman 2012-2014). dx/dt = f(x) + I(t).
   Input cancels the flow and *parks* the state at a fixed point = initial condition; removing the input releases
   autonomous dynamics that unfold into a movement. Preparation is silent because it lives in the *output-null space*
   of the readout (neurons >> muscles); action = the trajectory leaving the null space along output-potent directions.
   No separate gate. Relevance: L3 needs act(); action could be just the output-potent projection of the same field,
   and "wanting/planning" = where the state is parked.
4. Thousand Brains (Hawkins, Numenta). Cortex = one canonical module (column) replicated; each column builds its own
   predictive model in reference frames; columns vote. Scaling by replicating one unit, not by designing more parts.
5. Small-world graphs with hubs (Watts & Strogatz 1998; Bullmore & Sporns 2009). Brains, gene and social networks show
   high clustering (dense local modules) + short path length (a few long-range shortcuts) + heavy-tailed degree (hubs),
   at every scale. Read as the outcome of a trade-off: computation and integration vs wiring cost; also robust to
   random damage, fragile at hubs. Note: the number of edges stays far below n^2, so a law that produces this
   on its own would also meet the sub-quadratic growth goal.
