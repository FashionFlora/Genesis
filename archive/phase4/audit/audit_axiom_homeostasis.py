"""Audit whether the leaderboard leader needs its causal memory trace."""
import importlib.util
import json
from pathlib import Path

import torch

from sandbox.organism_judge import run_life, _summary
from sandbox.worlds.organism import OrganismWorld

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "candidates/axiom_causal_homeostasis/principle_organism.py"
# Diagnostic paired run: fewer independent worlds than the official judge.
# The official 8x128 run is already recorded in leaderboard.jsonl.
BATCH = 8
SEEDS = range(1)
STEPS = 6000


def load_variant(name):
    source = SOURCE.read_text()
    if name == "no_memory":
        source = source.replace(
            'memory = self.params["trace_rate"] * energy[:, None] * self.trace',
            'memory = torch.zeros_like(self.trace)')
    elif name == "no_turn":
        source = source.replace(
            'turn = torch.atan2(vertical, horizontal) / math.pi',
            'turn = torch.zeros_like(horizontal)')
    namespace = {"__name__": "audit_" + name}
    exec(compile(source, str(SOURCE), "exec"), namespace)
    return namespace["OrganismBrain"]


def measure(name):
    rows = []
    cls = load_variant(name)
    for seed in SEEDS:
        brain = cls(302, OrganismWorld.N_SENSORS, OrganismWorld.N_MOTORS,
                    BATCH, "cpu", seed=seed + 1729)
        rows.append(run_life(brain, BATCH, "cpu", seed * 101 + 7,
                             interoception=True, steps=STEPS, n_units=302))
    summary = _summary(rows, 302)
    return {key: summary[key]["mean"] for key in
            ("rooms_reached", "survival", "mean_energy", "reversal_latency", "place_memory")}


def measure_baseline(mode):
    rows = [run_life(None, BATCH, "cpu", seed * 101 + 7,
                     interoception=True, baseline=mode, steps=STEPS, n_units=302)
            for seed in SEEDS]
    summary = _summary(rows, 302)
    return {key: summary[key]["mean"] for key in
            ("rooms_reached", "survival", "mean_energy", "reversal_latency", "place_memory")}


if __name__ == "__main__":
    print(json.dumps({"steps": STEPS, "batch": BATCH,
                      "signed": measure("signed"),
                      "no_memory": measure("no_memory")}, sort_keys=True))
