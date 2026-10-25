# Genesis

**A small society of AI agents searching for the principle from which a developing organism, and its intelligence, can grow.**

Most learning systems are assembled: a fixed architecture, a loss, a gradient, and a module bolted on for every missing
ability (memory here, exploration there). Genesis asks the opposite question. Is there one law, or a few that interlock
as in a real brain, from which growth, pruning, learning, memory and exploration all *follow*? Two constraints are
final: **no reward from the world** and **no backpropagation**. The brain's architecture must shape itself.

The long-term yardstick is [Crafter](https://arxiv.org/abs/2109.06780) without reward. The intermediate yardstick is
biological: a simulated organism that, like a nematode or a fruit fly, has to find food, learn what is edible, relearn
when the world changes and remember places, all within one life.

---

## How it works

<p align="center"><img src="docs/agent-loop.svg" width="100%" alt="Agent loop"></p>

Language-model agents (Codex CLI, `gpt-6.1-sol`) propose principles and write them down as code. **Opinion never
decides:** a deterministic judge scores every candidate, and a critic assumes that each "new" idea already exists and that
each good result is an artefact until an ablation shows otherwise.

| Agent | Role |
|---|---|
| **Discoverer · life** | Starts from life itself: resources, metabolism, division, death. |
| **Discoverer · axioms** | Starts from the conditions any self-building, ever-learning system must satisfy. |
| **Discoverer · agency** | Starts from action. |
| **Discoverer · growth** | Units and connections appear only where the world needs them and vanish when they do not. |
| **Discoverer · dynamics** | Starts from the physics of dynamical systems. |
| **Biologist** | Distils principles from neuroscience and developmental biology, with opened sources. |
| **Experimenter** | Replicates results independently. |
| **Critic** | Searches for prior art, smuggled mechanisms and attempts to game the judge. |
| *World builder* | A separate agent that alone may change the judge and the world. |

The charter ([`CLAUDE.md`](CLAUDE.md)) is deliberately short: the goal, the two hard constraints, "I don't know is a
valid result", check prior art before building, every claimed effect needs an ablation, and each agent keeps a short
`RULES.md` of what its own results taught it. The agents are not told what an internal drive should be or what any
signal means: that is what they are looking for.

Each turn is a fresh session. Memory lives in files: a `HANDOFF.md` per agent, a shared message board
([`shared/board.jsonl`](shared/board.jsonl)) and a hypothesis registry ([`shared/hypotheses.json`](shared/hypotheses.json))
in which every idea moves from *proposed* to *testing* to *supported* or *refuted*. Each discoverer works on its own
"island" and crosses with other islands only now and then, after an early phase in which a shared leaderboard made
everyone converge on clones of one rule.

## The main test: one developing organism

The organism world ([`sandbox/worlds/`](sandbox/worlds/), judge [`sandbox/organism_judge_v7.py`](sandbox/)) is a flat
2D world on the GPU in which 1024 independent organisms live at once, one brain each.

- **Body and senses.** A simple eye of directional RGB pixels covering 360°, optionally the body's own energy level, and
  muscles for turning, driving (forward, stop, backward) and biting. The world never says what anything means and never
  gives a reward. Energy falls with time and movement, rises with the right food, and at zero the organism dies.
- **One organism that develops.** Intelligence is treated as the organization of a whole organism, not a separate thing
  inside a brain. The organism starts simple, lives on a yolk-like energy reserve while it develops, may grow its own
  body (more eye pixels, more muscles) at an energy cost, and passes through six *stages of ability* in one continuous
  life of 50 000 steps: finding food, association, context, place memory, concepts, maps. Animals appear only as a
  comparative footnote ("this ability is seen in…"), never as separate tasks.
- **Even the first stage defeats a table.** Whether a colour is food depends on a visible context (the wall pattern),
  drawn at random in every world, so a fixed value per colour (the Rescorla–Wagner rule) is useless by construction.
- **A skull, not a size.** `n_units` is only an upper limit. The judge records the actual size of brain and body during
  life (`growth`) and whether the organism falls into a routine (`routine`); both are observations, not scores.

### Calibration

Negative controls must fail and a positive control must pass, or the test is not measuring learning. Only the positive
controls are given a reward signal, and they are never ranked. Fraction of 1024 worlds reaching each stage (v7):

| Stage reached | 2 | 3 | 4 | 5 | 6 |
|---|---:|---:|---:|---:|---:|
| Random movement | 0% | 0% | 0% | 0% | 0% |
| Hard-wired reflex | 0.5% | 0.2% | 0% | 0% | 0% |
| Fixed value per colour, with reward | 2.3% | 0.6% | 0% | 0% | 0% |
| **Growing memory (colour × context, places), with reward** | **93.1%** | 86.4% | 67.8% | 5.9% | 1.5% |

## Results so far (25 October 2026)

| Candidate | Author | Stage score (v7) | Without its learning |
|---|---|---:|---:|
| `dynamics_metabolic_retention` | discoverer · dynamics | 0.80 | similar parent |
| `axiom_metabolic_retention_budget` | discoverer · axioms | 0.79 | **0.79** |
| `life_metabolic_fixed_scale_budget` | discoverer · life | 0.38 | — |
| `life_metabolic_adaptive_retention_budget` | discoverer · life | 0.29 | 0.08 |
| `dynamics_volatility_budget` | discoverer · dynamics | 0.27 | 0.08 (unmatched) |

What this says, honestly:

- **The top scores do not come from learning.** The leading candidate scores the same with its learning switched off.
  Most candidates are hand-written controllers for this particular world ("pixels 0–3 are the context", "three colours",
  brightness thresholds) with a small learning rule attached. That is why the brain size limit changes nothing: identical
  behaviour at 302 and at 100 000 units.
- **Where learning does help, it is one family of ideas:** an energy change after an action writes a trace of what was
  seen and done, and the body's reserve decides how long the trace lasts. This is close to known three-factor learning
  rules (an eligibility trace gated by a neuromodulator-like signal).
- **Nothing reaches stages 5–6**, and no brain grows. In the earlier world (v4), several candidates went further than a
  reward-trained control, but they turned out to be the Rescorla–Wagner rule rediscovered: one value per colour.

## What we learned about doing this

- **Building a world that measures the right thing is the hard part.** Writing the world took an hour; making it honest
  took two days. Calibration in both directions caught invisible-but-depleted food, a colour flip that reset every world,
  a reward hook any candidate could use, one shared brain for all organisms, and a positive control (PPO) too sample-hungry
  for a single life.
- **Agents optimise the world, not the goal.** Whatever the world allows, they find: a value table, a pixel decoder, a
  silent switch to the CPU to skip the GPU queue. Every fix moved the problem rather than removing it.
- **Speed matters as much as ideas.** A full evaluation takes over an hour, so a discoverer tests about ten ideas a night.
  Successful automated discovery of learning rules in the literature searched thousands to millions of variants.

## Next

- **A test that the candidate does not know the world:** sensor and motor channels shuffled at random in every world,
  so a controller that hard-codes "pixels 0–3 are the context" falls apart, while a principle that discovers what its
  inputs mean does not. A real brain does not know in advance which nerve does what.
- **A quick evaluation mode** and evolution under the agents: a discoverer writes a *family* of principles with open
  parts, and [`sandbox/evolve.py`](sandbox/) searches thousands of its versions on the GPU, selecting only between
  generations, never within a life.

## History

| Phase | What happened | Record |
|---|---|---|
| 1 (22–23 Oct) | Sensory streams, Snake, Crafter ladder. Prediction alone does not yield wanting (40 of 40 paired worlds); most local rules collapsed into a Hebbian covariance rule; three attempts to game the judge were caught. | [`archive/phase1/`](archive/phase1/) |
| 2 (23 Oct) | Clean start on streams; stopped after 20 minutes to build a better world. | [`archive/phase2/`](archive/phase2/) |
| 3 (23 Oct) | First organism world (v2); stopped when even the reward-trained control barely passed the first room. | [`archive/phase3/`](archive/phase3/) |
| 4 (24 Oct) | Calibrated organism world (v3/v4). Reward-free rules beat the reward-trained control, but all were one value per colour. | [`archive/phase4/`](archive/phase4/) |
| 5 (24–25 Oct) | Worlds v6/v7: context from the first room, one developing organism with stages of ability, body growth, yolk. | this repository's root |

A separate *archaeologist* agent began re-testing phase-1 mechanisms at large scale; its only measured mechanism did not
improve with scale ([`archive/archeology/`](archive/archeology/)).

## Repository map

| Path | Contents |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | the agents' charter (also `AGENTS.md`) |
| [`sandbox/`](sandbox/) | the judge, the organism world, its tests and calibration (the full leaderboard is over 5 MB and is not mirrored) |
| [`candidates/`](candidates/) | candidates, baselines and calibration controls |
| [`theory/`](theory/) | the discoverers' theories, journals, simulations and `RULES.md` |
| [`audit/`](audit/) | critiques, ablation scripts, tournament verdicts |
| [`biology/`](biology/) | biological principles with sources |
| [`shared/`](shared/) | board, hypothesis registry, idea bank, literature tool |
| [`agents/`](agents/) | supervisor, world-builder tasks, automation scripts |
| [`archive/`](archive/) | earlier phases in full, and the archaeologist's re-tests |

Working notes, prompts and the message board are partly in Polish, the project's working language.
