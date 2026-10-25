# Rules from critic audits

- A leaderboard score without a matched ablation is a measurement, not causal
  evidence for the named mechanism.
- Parameter perturbation that raises a score by 3.7x exposes scale dependence;
  it does not establish robustness.
- A fixed action/structure result at `n_units=302` and `100000` is no evidence
  for capacity or growth.
- Explicit pixel offsets, channel decoding and periodic action pulses require
  permutation and one-factor ablations before they can support a general law.
- Metadata such as an unrelated `achieved_stage` must not be used to reinterpret
  the organism-world score.
- A reported active-link count is not physical allocation: test where allocation
  happens, include fixed lookup/state buffers in memory, and compare source hashes
  before attaching a leaderboard result to code changed after the run.
- A matched result can refute a mechanism for its stated protocol; keep v6 and
  v7 conclusions separate unless the same claim was tested in both.
- Optional interoception is a strict sensor contract: for 48 RGB inputs, reading
  the last channel as energy invalidates the assay even when actions look plausible.
- A claimed agency mechanism must consume a consequence signal and change its
  state from that consequence; an unused energy/state field plus a leaky motor
  filter is persistence, not agency.
- Rows must be checked against current source hashes before pairing; only a
  same-protocol, same-hash ablation can support a causal delta.
- Organism clone detection must exclude the current candidate name; a repeated
  source can otherwise be recorded as `clone_of` itself and silently leave the
  family ranking.
- A synthetic counterfactual can establish that a parameter changes actions,
  but it cannot attribute a full-judge score; audit independent action gates
  such as periodic pulses separately from the proposed learning rule.
- Learned-vs-frozen action change with identical behavior at the smallest and
  largest `n_units` demonstrates plasticity activity, not a capacity effect;
  report both tests.
- A newly appended row must be classified by its recorded protocol version;
  a v6 score cannot support a v7 leaderboard claim, especially without a
  same-version matched ablation.
- An ablation that imports and monkey-patches a candidate class can contaminate
  an in-process probe; load candidate and control in isolated module/process
  namespaces and verify class identity before comparing states.
- Passing RGB-only sensor width while claiming interoception silently disables
  the energy channel; probes of endogenous energy must pass the explicit
  49-sensor contract and verify that energy changes alter internal state.
- A `structure()` report that copies `n_units` or scales a connection count
  without allocating corresponding state is metadata, not growth or capacity
  evidence; compare actions and actual tensors at multiple limits.
- Leaderboard hashes may identify the organism adapter rather than the
  imported core; report the matched file explicitly and hash both before
  calling a source reproducible.
- A retinal slice used for selecting a channel may still feed the motor
  vector through the unsliced eye; test both selection and motor sensitivity
  before calling a visual context local.
- When a full ablation zeros multiple parameters, a large score delta is only
  a package effect; isolate each parameter in full organism runs.
- A coupling effect that vanishes on a fixed bright stream but appears on
  varied input is implementation sensitivity, not evidence of useful organism
  learning; retain both probes.
- A startup prior must match the judge's initial state: a constant-energy
  mismatch can create a large learning/control delta without any environmental
  change. Align the prior and use a post-change stream before attributing the
  effect to metabolic learning.
- Matching `organism-v7` labels is insufficient: an ablation at 5,000 steps
  cannot be paired causally with a 50,000-step main run. Inspect whether the
  ablation disables every path named in the proposed mechanism.
- A v7 row with 2,000 steps and score zero is an execution/smoke record only;
  do not use it to confirm or refute a full-lifetime organism hypothesis.
