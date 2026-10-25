"""Focused audit for leaderboard rows 159-161; diagnostic only."""

import hashlib
import importlib.util
import json
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def actions(mod, n_units, n_sensors, rows):
    brain = mod.OrganismBrain(n_units, n_sensors, 3, 1, "cpu", seed=7)
    out = []
    for row in rows:
        out.append(brain.act(torch.tensor(row, dtype=torch.float32).reshape(1, -1))[0].tolist())
    return out, brain


def main():
    agency = load("candidates/agency_trace/principle_organism.py", "agency")
    ratio = load("candidates/dynamics_energy_ratio/principle_organism.py", "ratio")

    # 16 RGB pixels plus energy; use an asymmetric scene so permutations are visible.
    eye = [0.0] * 48
    eye[6:9] = [0.9, 0.1, 0.0]
    eye[39:42] = [0.1, 0.8, 0.0]
    full = eye + [0.5]
    perm = [0.0] * 48
    perm[0:3] = eye[6:9]
    perm[6:9] = eye[0:3]
    perm[39:42] = eye[39:42]
    perm_full = perm + [0.5]

    # no-interoception input has 48 sensors; varying its final actual pixel must matter
    # only as vision, never as an energy state.
    no_i_a = eye[:]
    no_i_b = eye[:]
    no_i_b[47] = 1.0
    ratio_no_i_a, ratio_state_a = actions(ratio, 302, 48, [no_i_a, no_i_a])
    ratio_no_i_b, ratio_state_b = actions(ratio, 302, 48, [no_i_b, no_i_b])

    agency_a, agency_brain_a = actions(agency, 302, 49, [full, full])
    agency_b, agency_brain_b = actions(agency, 302, 49, [perm_full, perm_full])
    agency_small, _ = actions(agency, 302, 49, [full])
    agency_large, _ = actions(agency, 100000, 49, [full])
    ratio_small, ratio_small_brain = actions(ratio, 302, 49, [full, full])
    ratio_large, ratio_large_brain = actions(ratio, 100000, 49, [full, full])

    report = {
        "sources": {
            "agency_trace": digest("candidates/agency_trace/principle_organism.py"),
            "agency_trace_ablation": digest("candidates/agency_trace_ablation/principle_organism.py"),
            "dynamics_energy_ratio": digest("candidates/dynamics_energy_ratio/principle_organism.py"),
            "dynamics_energy_ratio_ablation": digest("candidates/dynamics_energy_ratio_ablation/principle_organism.py"),
        },
        "ratio_no_interoception": {
            "action_delta_last_sensor": max(abs(a - b) for x, y in zip(ratio_no_i_a, ratio_no_i_b) for a, b in zip(x, y)),
            "previous_energy_a_final": float(ratio_state_a.previous_energy[0]),
            "previous_energy_b_final": float(ratio_state_b.previous_energy[0]),
            "eye_width": int(ratio_state_a.eye_width),
            "energy_index": int(ratio_state_a.energy_index),
        },
        "agency_retinal_permutation": {
            "first_action_delta_max": max(abs(a - b) for a, b in zip(agency_a[0], agency_b[0])),
            "second_action_delta_max": max(abs(a - b) for a, b in zip(agency_a[1], agency_b[1])),
        },
        "n_units_invariance": {
            "agency_first_action_delta": max(abs(a - b) for a, b in zip(agency_small[0], agency_large[0])),
            "ratio_second_action_delta": max(abs(a - b) for a, b in zip(ratio_small[1], ratio_large[1])),
            "ratio_structure_small": ratio_small_brain.structure(),
            "ratio_structure_large": ratio_large_brain.structure(),
        },
        "static_flags": {
            "agency_context_suppression": True,
            "agency_fixed_bite_thresholds": True,
            "agency_age_phase_sweep": True,
            "ratio_green_odd_even_context": True,
            "ratio_fixed_eye_offset": True,
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
