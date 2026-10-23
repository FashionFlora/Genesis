"""Compact provenance and action-dependency audit for leaderboard entries 599 onward."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def action_dependencies(path):
    tree = ast.parse(path.read_text())
    node = next((n for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef) and n.name == "act"), None)
    if node is None:
        return None
    names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
    attrs = {n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)}
    return {
        "observation_read": bool(names & {"obs", "observation"}),
        "prediction_read": "prediction" in names or "prediction" in attrs,
        "action_trace_read": bool(names & {"action_edges", "action_error", "returned", "count"})
                             or bool(attrs & {"action_edges", "action_error", "action_mass", "returned", "count"}),
        "snake_geometry": sorted(names & {"body", "head", "moves", "direction"}),
        "apple_or_length_names": sorted(names & {"apple", "apples", "length", "snake_length"}),
        "all_active_sensory_bits": "active" in names,
        "sensory_hash_tiebreak": "address" in names,
        "explicit_exploration": "exploration" in names or "exploration" in attrs,
    }


def main():
    rows = [json.loads(line) for line in (ROOT / "sandbox/leaderboard.jsonl").read_text().splitlines()]
    report = []
    for index in range(599, len(rows) + 1):
        row = rows[index - 1]
        path = ROOT / "candidates" / row["candidate"] / "principle.py"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        components = row.get("score_components", {})
        report.append({
            "entry": index,
            "candidate": row["candidate"],
            "author": row.get("author"),
            "score": row.get("score"),
            "highest_passed_level": row.get("highest_passed_level"),
            "reported_score_level": row.get("reported_score_level"),
            "stop_reason": row.get("stop_reason"),
            "clone_of": row.get("clone_of"),
            "source_hash_matches": digest == row.get("principle_sha256"),
            "principle_sha256": digest,
            "robustness": row.get("robustness"),
            "prediction_skill": components.get("prediction_skill_vs_constant"),
            "learning_improvement": components.get("learning_improvement"),
            "mean_apples": components.get("mean_apples_eaten"),
            "memory_scaling_exponent": row.get("phenomena", {}).get("memory_scaling_exponent"),
            "action": action_dependencies(path),
        })
    output = ROOT / "audit" / "audit_entries_20261023_latest_result.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
