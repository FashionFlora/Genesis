"""Small causal probes for leaderboard entries 557-560.

The probes do not replace judge scores: they expose direct sensory tie-breaks,
hash-addressed contexts, and score/hash provenance.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(candidate):
    path = ROOT / "candidates" / candidate / "principle.py"
    spec = importlib.util.spec_from_file_location("probe_" + candidate, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def snake_obs(index=None, width=700):
    obs = [0] * width
    # Keep a fixed head/body pair; toggle one otherwise identical sensory bit.
    obs[55] = 1
    obs[400 + 55] = 1
    if index is not None:
        obs[index] = 1
    return obs


def action_probe():
    system = load("contextual_predictive_closure").System()
    baseline = snake_obs()
    # Initialise width and then ask before any action-conditioned cell exists.
    system.step(baseline)
    probes = {}
    for index in [None, 11, 12, 500, 501, 600, 601]:
        try:
            probes[str(index)] = {"action": system.act(snake_obs(index))}
        except Exception as exc:  # record the public failure instead of hiding it
            probes[str(index)] = {"error": type(exc).__name__ + ": " + str(exc)}
    # A second step still leaves action-conditioned cells absent for new contexts.
    system.step(baseline)
    try:
        probes["after_second_step_11"] = {"action": system.act(snake_obs(11))}
    except Exception as exc:
        probes["after_second_step_11"] = {"error": type(exc).__name__ + ": " + str(exc)}
    # The intended tie-break, with the obvious integer cast applied, is a
    # direct weighted sensory address rather than learned action evidence.
    probes["int_cast_tiebreak"] = {
        str(index): int(sum((i + 1) * bit for i, bit in enumerate(snake_obs(index))) % 4)
        for index in [None, 11, 12, 500, 501, 600, 601]
    }
    return probes


def context_probe():
    system = load("predictive_context_sufficiency").System()
    width = 8
    # Same target transition, but context address differs by the second half.
    a = [0, 0, 0, 0, 0, 0, 0, 0]
    b = [0, 0, 0, 0, 1, 0, 0, 0]
    c = [0, 0, 0, 0, 0, 0, 0, 1]
    system.step(a)
    p_b = system.step(b)
    p_c = system.step(c)
    return {
        "context_a": sum(a[width // 2:]) % 8,
        "context_b": sum(b[width // 2:]) % 8,
        "context_c": sum(c[width // 2:]) % 8,
        "prediction_after_b": p_b,
        "prediction_after_c": p_c,
        "memory_bytes": system.structure()["memory_bytes"],
    }


def provenance():
    rows = [json.loads(line) for line in (ROOT / "sandbox/leaderboard.jsonl").read_text().splitlines()]
    out = {}
    for number in (557, 558, 559, 560):
        row = rows[number - 1]
        path = ROOT / "candidates" / row["candidate"] / "principle.py"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        out[str(number)] = {
            "candidate": row["candidate"],
            "author": row.get("author"),
            "clone_of": row.get("clone_of"),
            "score": row.get("score"),
            "highest_passed_level": row.get("highest_passed_level"),
            "reported_score_level": row.get("reported_score_level"),
            "stop_reason": row.get("stop_reason"),
            "leaderboard_sha": row.get("principle_sha256"),
            "current_sha": digest,
            "sha_matches": digest == row.get("principle_sha256"),
        }
    return out


def main():
    result = {
        "provenance": provenance(),
        "context_probe": context_probe(),
        "action_probe": action_probe(),
    }
    path = ROOT / "audit/new_entries_20261023_result.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
