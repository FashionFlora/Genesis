# Genesis

**A small society of AI agents searching for a single principle from which a living, learning system can grow.**

Most learning systems are assembled: a fixed architecture, a loss, a gradient, and a module bolted on for every missing
ability (memory here, exploration there). Genesis asks the opposite question. Is there one law, in the way one physical
law accounts for many phenomena, from which growth, pruning, learning, memory and exploration all *follow*? The system
must work **without external reward** and **without backpropagation**, and its structure must build itself. Biology is
the main source of inspiration.

The long-term yardstick is [Crafter](https://arxiv.org/abs/2109.06780) without reward. The first honest milestone is
modest: beat the best reward-free result from the Crafter paper, Plan2Explore at 2.1%, without reward and without
backprop. Humans score about 50%.

---

## How it works

<p align="center"><img src="docs/agent-loop.svg" width="100%" alt="Agent loop"></p>

Language-model agents (Codex CLI) propose principles and write them down as code. **Opinion never decides:** a
deterministic sandbox scores every candidate, and the critic exists to assume that each "new" idea already exists and
that each good result is an artefact until shown otherwise.

| Agent | Role |
|---|---|
| **Discoverer · life** | Starts from life itself: resources, metabolism, division, death. |
| **Discoverer · axioms** | Starts from the conditions any self-building, ever-learning system must satisfy. |
| **Experimenter** | Replicates results independently and ports principles to the judge's format. |
| **Critic** | Searches for prior art, smuggled mechanisms and attempts to game the judge. |
| *Biologist (earlier phase)* | Distilled principles from neuroscience and developmental biology into [`biology/PRINCIPLES.md`](biology/PRINCIPLES.md). |

Each turn is a fresh session. Memory lives in files: a short `HANDOFF.md` per agent, a shared message board
([`shared/board.jsonl`](shared/board.jsonl)) and a hypothesis registry ([`shared/hypotheses.json`](shared/hypotheses.json))
in which every idea moves from *proposed* to *critiqued* to *testing* to *supported* or *refuted*. Following current
practice in AI-scientist systems such as Google's Co-Scientist and AlphaEvolve, the best candidates return to the
discoverers as parents to be mutated or crossed, and the critic runs pairwise tournaments on what the judge cannot
measure: how fundamental an idea is, and how new.

## The judge

<p align="center"><img src="docs/judge.svg" width="100%" alt="The judge"></p>

A candidate is a single file, `candidates/<name>/principle.py`. The judge, in [`sandbox/`](sandbox/), is plain code:

- **Worlds, in order.** Sensory streams whose regimes change and return, then harder streams, then reward-free Snake,
  then reward-free Crafter. Each level counts only if the previous gate was passed.
- **Behaviour.** Prediction, adaptation after change, memory when an old regime returns, whether structure tracks the
  complexity of the world, and cost.
- **Elegance.** Every constant or branch hidden outside the declared `PARAMS` is penalised.
- **Robustness.** Parameters are allowed, but the judge perturbs each one by a random factor in [0.5, 2] and checks that
  the phenomena survive. A principle that works only when finely tuned is not a principle.
- **Learning.** The end of a run must beat its start, so a hand-written strategy cannot pass.

In progress: a *grokking* probe that holds out combinations of a hidden rule to see whether a system can, after a long
silence, suddenly generalise; a long GPU track for late bloomers; and a scaling test from 8 to 64 channels.

## What we have found so far

<p align="center"><img src="docs/resource-flow.svg" width="100%" alt="The resource-flow principle"></p>

- **Resource flow (H003 → H005)** is the most promising line. A single mass balance per cell (intake minus upkeep minus
  the cost of its own prediction error) produces growth by division, pruning by death, and selection of useful
  connections, with no age clock, no population cap and no fitness threshold. In a small world it clearly beats matched
  controls: 90% vs 37% of cells on the relevant signal, in 20 of 20 seeds. In a larger world it still **loses to a plain
  Hebbian rule**, and learning and variation are not yet derived from the same law.
- **Coactivity-gated sprouting (H001)** is supported with 8 channels and weakens with 16.
- **Minimum description length (H002)** and two further hypotheses were refuted, two of them by their own authors.
- **Three attempts to game the judge** were caught: a hard-coded Hamiltonian cycle in Snake, constants hidden as strings,
  and a hand-written path search. They are kept, with explanations, in
  [`sandbox/disqualified.tsv`](sandbox/disqualified.tsv), because Goodhart's law turned out to be one of the project's
  most instructive results.

Honestly, these are careful variants of known ideas (Darwinian selection, MDL, synaptic tagging, homeostasis) in toy
worlds, not yet a new paradigm. The full critiques live in [`audit/`](audit/).

## Repository map

| Path | Contents |
|---|---|
| [`theory/`](theory/) | the discoverers' theories, journals and simulations |
| [`audit/`](audit/) | critiques, prior-art reviews, tournament verdicts |
| [`biology/`](biology/) | biological principles with sources |
| [`sandbox/`](sandbox/) | the judge, leaderboard and disqualifications |
| [`candidates/`](candidates/) | candidates, baselines and the test cheats |
| [`shared/`](shared/) | board, hypothesis registry, idea bank, literature tool |
| [`engine/`](engine/) | stream benchmarks and the Crafter harness |
| [`agents/`](agents/) | supervisors and agent prompts |
| [`registry/`](registry/) | literature catalogue from the first phase, kept as memory against repetition |

Working notes, prompts and the message board are partly in Polish, the project's working language.
