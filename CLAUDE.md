# Genesis

**Goal:** a fundamental principle (or a few that interlock, as in the brain) from which digital biointelligence follows on
its own: a system that grows, prunes itself, learns, remembers and explores, without external reward and without
backpropagation. Do not bolt on a separate mechanism for each ability. Look for the law, or the few laws, they follow from. This may require new mathematics. The answer is probably
neither simple nor obvious, and probably nothing you have seen before: if your idea resembles something you know, that is
a reason to look further, not a result. A turn may end with "I don't know" and what is missing; that is better than
another variant of something known. Before you build an idea, check with `shared/lit.py search` whether it already
exists; the critic only double-checks. You are a team: build on each other's results, and you may co-develop one
principle with another agent (propose it on the board, agree who does what). The goal is a few interlocking laws at most, not a merge of modules. Failing in a small world does not refute an idea whose
mechanism needs scale (for example, but not necessarily, phase transitions or capacity): small worlds only check that the code runs and is not a
clone; test such ideas directly at large scale on the GPU (`judge.py --gpu`, once announced on the board).
Biology
(biology/PRINCIPLES.md) is a source of inspiration.

**Anchor:** only what was actually run counts. Numbers come only from result files. A refuted idea is also a result.
Facts from the literature only from sources you opened (`.venv/bin/python shared/lit.py search|arxiv|fetch|github`).

**Judge:** `.venv/bin/python sandbox/judge.py candidates/<name>` (contract in sandbox/README.md). Parameters in `PARAMS`
are allowed, but the judge tests robustness to changing them. Hidden constants and branches are penalised. Leaderboard:
sandbox/leaderboard.jsonl. Do not modify sandbox/. Hand-written strategies and any attempt to game the judge lead to
disqualification (sandbox/disqualified.tsv).

**Token economy:** every token is paid. Read only the lines you need (`rg`, `sed -n a,bp`, `head`), print summaries
instead of whole files or raw JSON results, and batch related shell commands into one step.

**Shared tools:** board `python3 shared/board.py read|post <me> ...` (short and concrete), hypotheses
`python3 shared/hyp.py list|add|status|note`.

**Memory between turns:** every turn is a new session. Start from your `HANDOFF.md` and finish by overwriting it briefly
(at most 25 lines): what you did, what came out (numbers and paths), what comes next.

**Server limits (shared with a TTS dataset pipeline):** write only inside `/opt/dlami/nvme/genesis/`, in your own files.
Never touch `/opt/dlami/nvme/dataset/`, other processes or other tmux sessions. GPU allowed (run `nvidia-smi` first,
max 40 GB). Python only from `.venv`. Run long commands with `nice -n 15`, max ~6 GB RAM and 3 cores.

The working language of the board and notes may be Polish or English.
