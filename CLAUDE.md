# Genesis

**Goal:** find what digital biointelligence follows from: a system that grows, prunes itself, learns, remembers and
explores, without external reward and without backpropagation. One law or a few, not a module per ability. It is
probably nothing you have seen before; "I don't know" is a valid result. Check prior art before you build. You are a
team. A small world cannot refute an idea that needs scale.
Biology is a source of inspiration.

**Anchor:** only what was actually run counts. Numbers come only from result files. A refuted idea is also a result.
Every claimed effect needs an ablation. Keep a short `RULES.md` of what your own results taught you.
Facts from the literature only from sources you opened (`.venv/bin/python shared/lit.py search|arxiv|fetch|github`).

**Main test:** the organism world: one continuous life in nested rooms of growing difficulty, sensing only through
simple eyes and, optionally, its own energy level; no reward from the world. Run
`nice -n 15 .venv/bin/python sandbox/judge.py candidates/<name> --organism --author <your agent name>` (contract and
options in sandbox/README.md). `n_units` (302 to 10^5) is only an upper limit, like the size of a skull, not a fixed brain size. Parameters in `PARAMS` are allowed, but the judge tests
robustness to changing them. Hidden constants and branches are penalised. Leaderboard: sandbox/leaderboard.jsonl
(track "organism"). Do not modify sandbox/. Hand-written strategies and any attempt to game the judge lead to
disqualification (sandbox/disqualified.tsv). Older stream/Snake/Crafter tracks still exist for quick checks.

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
