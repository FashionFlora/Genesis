# Crafter benchmark engine

Deterministic, reward-blind evaluation harness for Crafter. Python implementation uses Crafter's own deterministic seeded worlds and fixed policy RNG seeds.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install crafter torch
```

Crafter is installed from PyPI (`crafter`); this run used version 1.8.3 and torch 2.14.1. Torch is optional for random and pixel-novelty policies, but needed by candidate agents that use it.

## Agent API

Implement `act(obs) -> int` (0–16 for the installed 17-action Crafter environment) and `observe(obs, action, next_obs, done, info_bez_nagrody)`. Set a boolean class/instance attribute `uses_backprop`. Additional constructor kwargs `seed` and `action_count` are provided:

```python
class MyAgent:
    uses_backprop = False
    def __init__(self, seed=0, action_count=17): ...
    def act(self, obs): ...
    def observe(self, obs, action, next_obs, done, info_bez_nagrody): ...
```

`info_bez_nagrody` is an allowlist containing inventory, discount, semantic view and player position. Harness invokes `crafter.Env(reward=False)` and internally uses the raw environment's achievements only to compute evaluation metrics. The agent receives neither reward nor achievements in `act` or `observe`.

## Run

From the repository root:

```bash
PYTHONHASHSEED=0 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  nice -n 15 taskset -c 0-2 .venv/bin/python engine/run.py \
  --agent random --steps 100000 --episodes 10 --seed 1234
```

Smoke size is 100,000 total environment steps (multiple standard 10k episodes) per seed. Full-size protocol is 1,000,000 steps per seed (the standard Crafter benchmark budget) and should be launched only for random when it fits the 30-minute run limit. `--agent pixel_novelty` starts the reward-free curiosity reference. Candidate path syntax: `--agent package.module:ClassName`, with importable project module path. Set `--run-id` for a stable output folder name; otherwise a wall-clock id is generated. Result is `experiments/<run_id>/result.json`.

Each seed receives a fixed 100k-step (or user-set) total budget, which Crafter internally divides into episodes capped at its 10,000-step horizon, with reset on death/timeout. Seed list is `seed + episode_index` at the outer run level; the environment's internal episode reseeding is pinned by `PYTHONHASHSEED=0`. Policy RNG uses the initial seed.

## Stage 1: sensory-stream benchmark

`engine/stream_bench.py` implements the first ladder rung without Crafter. An agent follows `predict(observation) -> prediction` and then `observe(observation, next_observation)`; its target is the next sensory vector. The evaluator does not pass reward or regime labels. The default stream has three predictive relations (A, B, C), changes regimes every 1,000 transitions, and returns to A and B. Predictions are scored online with Brier/MSE error, with regime-wise adaptation and return-forgetting measurements. Structure snapshots, growth/pruning counts, a deterministic work proxy, estimated state bytes, and elapsed CPU/wall time are recorded.

Run from the repository root:

```bash
PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  nice -n 15 taskset -c 0-2 .venv/bin/python engine/stream_bench.py \
  --agents mean,persistence,fixed_hebb,growing --steps 6000 --replicates 5 \
  --output experiments/stream-stage1
```

The `mean` and `persistence` agents are minimal fixed baselines. `fixed_hebb` uses a fixed all-to-all network and centered local Hebbian updates. `growing` stores active input-to-predictor association units, adds units when a local correlation trace crosses a threshold, and prunes units whose trace remains weak. Crafter remains the third rung; the stream runner is independent of `engine/run.py`.

External stream agents can be loaded as `--agents engine.my_module:MyClass`. The class receives `input_dim`, `output_dim`, and `seed`; it implements `predict(observation)`, `observe(observation, next_observation)`, and `structure_metrics()`. The evaluator passes no reward or regime metadata to it.

The H001 source-neighborhood runner also supports larger neighborhoods as an exploratory scaling check. For example, this reproduces the N=16 run (the registered H001 thresholds apply to N=8, so N=16 does not decide the registered prediction):

```bash
PYTHONHASHSEED=0 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  nice -n 15 taskset -c 0-2 .venv/bin/python engine/sprouting_bench.py \
  --target-count 16 --regimes 16 \
  --replicates 20 --steps-per-regime 1500 \
  --seed 20272022 --output experiments/h001-neighborhood-16
```

### H001 local-sprouting replication

`engine/sprouting_bench.py` provides a source-neighborhood event stream with eight target channels for the coactivity-gated sprouting hypothesis. It records the target's mature-contact coverage, recovery to 50 consecutive contacts, null stable-contact rate, prediction error, structure, and cost. The `h001` agent implements the definition from `theory/theorist_axioms/THEORY.md`; `mean` and `fixed_hebb` are fixed controls.

Stable-contact metrics, including `target_coverage`, are `null` for controls that do not expose mature-contact state. Compare those controls by prediction error and their reported connection structure.

```bash
PYTHONHASHSEED=0 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  nice -n 15 taskset -c 0-2 .venv/bin/python engine/sprouting_bench.py \
  --replicates 20 --steps-per-regime 1500 --regimes 8 \
  --seed 20271022 --output experiments/h001-replication-controlled
```

## Metrics and integrity

Each achievement's success rate is fraction of episodes in which it was reached, times 100. Crafter score, following arXiv:2109.06780 Section 3.3, is `exp((1/N) * sum_i(log(1 + s_i))) - 1`, where `N=22` and `s_i` is success rate in percent. The cited paper's Table 1 reports Random: Score 1.6%, Return 2.1 ± 1.3 (return is not computed by this reward-free harness). A score calculated from a small episode count is coarse; use a broad fixed-seed evaluation for publication-quality comparisons.

The harness records the backprop declaration and scans reachable agent-owned objects for tensors with `requires_grad`. Candidate agents can also use `install_backward_audit()` / restore callback in `engine/agents.py` to count explicit `Tensor.backward()` calls. Detection gaps: calls to `torch.autograd.backward/grad`, functional/custom gradient engines, hidden tensors not reachable from agent state, native code, and a false declaration can evade or defeat this best-effort audit. The declared flag is not proof. GPU/CPU metadata and versions are recorded, but performance results should note CPU/GPU actually used by each agent.

Crafter score and achievement results are benchmark outputs—not training signals. The harness does not provide reward to candidate policies.
