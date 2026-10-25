"""Focused audit of the five newest organism leaderboard records."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
NAMES = [
    "axiom_global_capacity_covariance",
    "axiom_centered_correlation",
    "axiom_capacity_correlation_ablation",
    "agency_sensorimotor_prediction",
    "axiom_metabolic_retention_budget",
]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.OrganismBrain


def latest_rows():
    rows = {}
    with (ROOT / "sandbox/leaderboard.jsonl").open() as f:
        for line_no, line in enumerate(f, 1):
            row = json.loads(line)
            if row.get("candidate") in NAMES:
                rows[row["candidate"]] = {
                    "line": line_no,
                    "score": row.get("score"),
                    "protocol": row.get("protocol"),
                    "principle_sha256": row.get("principle_sha256"),
                    "clone_of": row.get("clone_of"),
                }
    return rows


def action_probe(cls, *, params=None, seed=19):
    b, s, m, t = 12, 49, 3, 64
    g = torch.Generator().manual_seed(303)
    stream = torch.rand(t, b, s, generator=g)
    brain = cls(302, s, m, b, "cpu", seed=seed, params=params)
    acts = torch.stack([brain.act(x).detach() for x in stream])
    return acts


def jsonable(value):
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist() if value.numel() > 1 else value.item()
    return value


def main():
    out = {"rows": latest_rows(), "candidates": {}}
    for name in NAMES:
        d = ROOT / "candidates" / name
        core = d / "principle.py"
        adapter = d / "principle_organism.py"
        src = core if core.exists() else adapter
        text = src.read_text()
        cls = load(src, "audit_" + name)
        hashes = {
            "principle.py": hashlib.sha256(core.read_bytes()).hexdigest() if core.exists() else None,
            "principle_organism.py": hashlib.sha256(adapter.read_bytes()).hexdigest() if adapter.exists() else None,
        }
        recorded_hash = out["rows"].get(name, {}).get("principle_sha256")
        small = cls(302, 49, 3, 12, "cpu", seed=19)
        large = cls(100000, 49, 3, 12, "cpu", seed=19)
        g = torch.Generator().manual_seed(303)
        stream = torch.rand(64, 12, 49, generator=g)
        a_small = torch.stack([small.act(x).detach() for x in stream])
        a_large = torch.stack([large.act(x).detach() for x in stream])
        item = {
            "source": str(src.relative_to(ROOT)),
            "source_sha256": hashes,
            "recorded_hash": recorded_hash,
            "recorded_hash_file": next((k for k, v in hashes.items() if v == recorded_hash), None),
            "structure_302": jsonable(small.structure()),
            "structure_100000": jsonable(large.structure()),
            "action_rmse_302_vs_100000": float((a_small - a_large).square().mean().sqrt()),
            "flags": {
                "hardcoded_eye_slice": "eye[:, 4:]" in text,
                "periodic_age_gate": "remainder(5)" in text or "age % 5" in text,
                "fixed_visual_thresholds": any(x in text for x in ("> 0.04", "> 0.10", "> 0.24", "> 1.25")),
                "manual_channel_or_context": any(x in text for x in ("argmax", "odd", "even", "green")),
                "sinusoidal_exploration": "sin(" in text,
                "structure_reports_limit_directly": "float(self.n_units)" in text,
            },
        }
        if name == "agency_sensorimotor_prediction":
            alt = action_probe(cls, params={"prediction_gain": 0.0})
            item["prediction_gain_zero_action_rmse"] = float((a_small - alt).square().mean().sqrt())
        if name == "axiom_metabolic_retention_budget":
            alt = action_probe(cls, params={"energy_coupling": 0.0})
            item["energy_coupling_zero_action_rmse"] = float((a_small - alt).square().mean().sqrt())
        out["candidates"][name] = item
    (ROOT / "audit/rows167_171_audit.result.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
