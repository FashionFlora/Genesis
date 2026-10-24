# Genesis

**A small society of AI agents searching for the principle from which a brain can grow.**

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

## The main test: the organism world

The organism world ([`sandbox/worlds/organism.py`](sandbox/worlds/organism.py), judge
[`sandbox/organism_judge.py`](sandbox/organism_judge.py)) is a flat 2D world on the GPU in which thousands of organisms
live at once.

- **Body.** Position and heading; three muscles: turn, drive (forward, stop or backward) and bite.
- **Senses.** Only a simple eye (16 directional RGB pixels covering 360°) and, optionally, the body's own energy level,
  like hunger. The world never says what anything means and never gives a reward. Energy falls with time and movement,
  rises when the organism eats the right thing, and at zero the organism dies.
- **One continuous life in nested rooms.** The organism starts in a small room. A room opens onto the next only when the
  organism has mastered it: it keeps its energy up and bites the right colour selectively after the meaning of colours
  has flipped. Later rooms add more food patches that deplete and regrow elsewhere (so it cannot graze in one spot
  forever), decoys, faster hunger, a looming shadow to escape and visual landmarks to remember places. Which colour is
  food is drawn at random in every world, so no strategy can be written in advance.
- **A skull, not a size.** `n_units` (302, as in *C. elegans*, up to 10⁵, roughly a fruit fly) is only an upper limit.
  The judge records the brain's actual number of units and connections during life (`growth`), and whether the organism
  gets stuck in a routine (`routine`). Both are observations only and do not change the score.
- **Every measurement uses at least 1024 worlds**, with 95% confidence intervals. Each organism must have its own brain:
  the judge perturbs one organism's input and checks that no other organism's output changes.

### Calibration: does the test measure learning at all?

A test that cannot register learning would make every principle look like a failure. So the world is calibrated in
both directions, borrowing a practice from automated wet labs: negative controls that must fail, and a positive control
that must pass. The positive control is the only thing allowed a reward signal (energy gain) and is never ranked.
Fraction of 1024 worlds reaching each room (organism-v3):

| Room reached | 2 | 3 | 4 | 5 | 6 |
|---|---:|---:|---:|---:|---:|
| Random movement | 0% | 0% | 0% | 0% | 0% |
| Hard-wired reflex ("go to colour") | 1.7% | 1.2% | 0.6% | 0% | 0% |
| Simple online delta rule | 8.1% | 5.9% | 2.2% | 0.9% | 0% |
| **Positive control** (learner with reward) | **76.8%** | 69.6% | 61.8% | 29.1% | 3.4% |

Getting here took far longer than writing the world. The calibration caught real bugs: depleted food that was still
visible to the eye, so a colour reflex passed by luck; a colour flip in one world that reset the flip clock in all of them;
a reward hook any candidate could have used. It also caught a mistake in the calibration itself: PPO, the first positive
control, needs hundreds of thousands of steps and lost to random movement within a single 6000-step life.

## Current results (phase 4, 24 October 2026)

Mean number of rooms reached (higher is better; organism-v4):

| Candidate | Author | Score | What it is |
|---|---|---:|---|
| `axiom_causal_homeostasis` | discoverer · axioms (replicated by the experimenter) | 2.85 | the energy change after an action reinforces or weakens the trace of what was seen |
| `metabolic_gate_fixed_speed` | discoverer · life | 2.84 | the body's energy gates how strongly a sensory trace is retained |
| `action_consequence` | discoverer · agency | 2.65 | energetic consequences strengthen stimulus–action pairs |
| positive control (with reward) | calibration | 2.41 | |

Several principles without any reward from the world now go further than the reward-trained control. Ablations say why:
removing the energy gate on the sensory trace drops `metabolic_gate` from 2.84 to 2.03; removing the action trace drops
`action_consequence` from 2.69 to 2.27. An energy-to-speed coupling that the critic flagged as a written-in policy turned
out to be *harmful*: taking it out raised the score from 2.40 to 2.84.

**The honest caveat:** every leading candidate keeps exactly **3 units from birth to death**. The `growth` measurement
shows that none of them grows or prunes. They are good learning rules in a small table, not architectures that shape
themselves, because the current rooms can be solved with one value per colour. That is a flaw of the world, not only of
the agents.

## In progress

- **Ability to reverse and stop** (organism-v4), with recalibration.
- **Evolution under the agents.** The agents reason well but search slowly: every successful attempt in the literature to
  discover learning rules automatically (evolved Hebbian rules, meta-learned plasticity, discovered RL algorithms)
  searched thousands to millions of variants. An agent will write a principle as a *family* with open parts, and
  [`sandbox/evolve.py`](sandbox/) will search thousands of its versions on the GPU. The world batch is the population,
  selection acts only between generations, never within a life, and the evolved version must still pass the normal
  judge.
- **Rooms a small table cannot pass:** many object kinds with new ones appearing during life, meanings that depend on
  context, and food out of sight that must be found again from memory. They come with a negative control (a fixed
  value-per-colour table must fail them) and a positive control (a learner whose memory grows must pass them).

## History

| Phase | What happened | Record |
|---|---|---|
| 1 (22–23 Oct) | Sensory streams, Snake, Crafter ladder. Prediction alone does not yield wanting (40 of 40 paired worlds); most local rules collapsed into a Hebbian covariance rule; three attempts to game the judge were caught. | [`archive/phase1/`](archive/phase1/) |
| 2 (23 Oct) | Clean start with no memory of phase 1, still on streams; stopped after 20 minutes to build a better world. | [`archive/phase2/`](archive/phase2/) |
| 3 (23 Oct) | First organism world (v2); stopped after an hour when calibration showed that even the reward-trained control could barely pass the first room. | [`archive/phase3/`](archive/phase3/) |
| 4 (24 Oct–) | Calibrated organism world (v3/v4), current results above. | this repository's root |

A separate *archaeologist* agent started re-testing every distinct phase-1 mechanism at large scale on the GPU, to ask
whether anything was discarded only because the worlds were too small. Its first and so far only measured mechanism did
not improve with scale; the rest is unfinished ([`archive/archeology/`](archive/archeology/)).

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
