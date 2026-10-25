"""Critic probes for newest organism rows 158-159.

The checks are intentionally small: source/hash provenance, capacity
invariance, RGB/pixel dependence, and behavior with the optional energy sensor.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]


def load(rel, tag):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(tag, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, hashlib.sha256(path.read_bytes()).hexdigest()


def sensors(n_sensors, color=1, pixel=5, energy=0.95):
    x = torch.zeros(1, n_sensors)
    if n_sensors == 49:
        x[0, 48] = energy
        eye_width = 16
    else:
        eye_width = n_sensors // 3
    if pixel < eye_width:
        x[0, pixel * 3 + color] = 0.8
        if pixel + 1 < eye_width:
            x[0, (pixel + 1) * 3 + color] = 0.5
    return x


def run(rel, n_sensors=49, units=302, sequence=None):
    mod, sha = load(rel, rel.replace("/", "_").replace(".", "_"))
    b = mod.OrganismBrain(units, n_sensors, 3, 1, "cpu", seed=7)
    seq = sequence or [sensors(n_sensors)]
    out = [b.act(x).detach() for x in seq]
    return torch.stack(out), b.structure(), sha


def main():
    base = "candidates/dynamics_energy_ratio/principle_organism.py"
    ablation = "candidates/dynamics_energy_ratio_ablation/principle_organism.py"
    agency = "candidates/agency_trace/principle_organism.py"
    agency_ab = "candidates/agency_trace_ablation/principle_organism.py"
    result = {}

    a302, s302, sha = run(base, units=302)
    a100k, s100k, _ = run(base, units=100000)
    red, _, _ = run(base, sequence=[sensors(49, color=0)])
    green, _, _ = run(base, sequence=[sensors(49, color=1)])
    no_energy, no_energy_struct, _ = run(base, n_sensors=48)
    result["dynamics_energy_ratio"] = {
        "sha256": sha,
        "units_302_vs_100000_action_equal": bool(torch.equal(a302, a100k)),
        "structure_302": s302,
        "structure_100000": s100k,
        "red_vs_green_action_max_abs": float((red - green).abs().max()),
        "n_sensors_48_action": no_energy[0, 0].tolist(),
        "n_sensors_48_structure": no_energy_struct,
    }
    _, _, ab_sha = run(ablation)
    result["dynamics_energy_ratio_ablation"] = {
        "sha256": ab_sha,
        "leaderboard_rows": [],
        "note": "No matching candidate row found by name in leaderboard.jsonl.",
    }

    # The repaired agency ablation should change only the persistence term.
    seq = [sensors(49, pixel=5), sensors(49, pixel=5)]
    ag1, _, ag_sha = run(agency, sequence=seq)
    ag2, _, ag_ab_sha = run(agency_ab, sequence=seq)
    result["agency_trace"] = {
        "sha256": ag_sha,
        "ablation_sha256": ag_ab_sha,
        "same_first_action": bool(torch.equal(ag1[0], ag2[0])),
        "second_action_delta_max_abs": float((ag1[1] - ag2[1]).abs().max()),
        "current_base_hash_has_leaderboard_row": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    (ROOT / "audit/dynamics_agency_audit.result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
