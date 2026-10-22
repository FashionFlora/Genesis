# Genesis

**Goal:** one fundamental principle from which digital biointelligence follows on its own: a system that grows, prunes
itself, learns, remembers and explores, without external reward and without backpropagation. Do not add separate
mechanisms. Look for the law from which they follow. This may require new mathematics. Biology
(biology/PRINCIPLES.md) is a source of inspiration.

**Anchor:** only what was actually run counts. Numbers come only from result files. A refuted idea is also a result.
Facts from the literature only from sources you opened (`.venv/bin/python shared/lit.py search|arxiv|fetch|github`).

**Judge:** `.venv/bin/python sandbox/judge.py candidates/<name>` (contract in sandbox/README.md). Parameters in `PARAMS`
are allowed, but the judge tests robustness to changing them. Hidden constants and branches are penalised. Leaderboard:
sandbox/leaderboard.jsonl. Do not modify sandbox/. Hand-written strategies and any attempt to game the judge lead to
disqualification (sandbox/disqualified.tsv).

**Shared tools:** board `python3 shared/board.py read|post <me> ...` (short and concrete), hypotheses
`python3 shared/hyp.py list|add|status|note`.

**Memory between turns:** every turn is a new session. Start from your `HANDOFF.md` and finish by overwriting it briefly
(at most 25 lines): what you did, what came out (numbers and paths), what comes next.

**Server limits (shared with a TTS dataset pipeline):** write only inside `/opt/dlami/nvme/genesis/`, in your own files.
Never touch `/opt/dlami/nvme/dataset/`, other processes or other tmux sessions. GPU allowed (run `nvidia-smi` first,
max 40 GB). Python only from `.venv`. Run long commands with `nice -n 15`, max ~6 GB RAM and 3 cores.

The working language of the board and notes may be Polish or English.
