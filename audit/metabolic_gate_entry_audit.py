"""Audit leaderboard row 173 and its unpublished matched control."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.OrganismBrain


def run(cls, n_units=302, sensors=49, batch=16, steps=96, seed=19, params=None, stream=None):
    if stream is None:
        g = torch.Generator().manual_seed(303)
        stream = torch.rand(steps, batch, sensors, generator=g)
    brain = cls(n_units, sensors, 3, batch, "cpu", seed=seed, params=params)
    acts = torch.stack([brain.act(x).detach() for x in stream])
    return acts, brain


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    main_path = ROOT / "candidates/dynamics_metabolic_gate/principle_organism.py"
    ctl_path = ROOT / "candidates/dynamics_metabolic_gate_ablation/principle_organism.py"
    Main = load(main_path, "metabolic_gate_main")
    Control = load(ctl_path, "metabolic_gate_control")
    g = torch.Generator().manual_seed(303)
    stream = torch.rand(96, 16, 49, generator=g)

    nominal, bm = run(Main, stream=stream)
    control, bc = run(Control, stream=stream)
    package, bp = run(Main, params={"energy_coupling": 0.0, "readiness_recovery": 0.0}, stream=stream)
    no_coupling, bn = run(Main, params={"energy_coupling": 0.0}, stream=stream)
    no_recovery, br = run(Main, params={"readiness_recovery": 0.0}, stream=stream)
    no_cost, bk = run(Main, params={"readiness_cost": 0.0}, stream=stream)
    large, bl = run(Main, n_units=100000, stream=stream)

    bright = torch.zeros(96, 16, 49)
    bright[:, :, 24] = 1.0  # one concentrated red pixel (pixel 8)
    bright[:, :, 48] = (torch.arange(96) % 2).float()[:, None]
    bright_main, bbm = run(Main, stream=bright)
    bright_no_recovery, bbr = run(Main, params={"readiness_recovery": 0.0}, stream=bright)
    bright_no_cost, bbc = run(Main, params={"readiness_cost": 0.0}, stream=bright)

    # Keep RGB pixels fixed and alter only the optional final energy sensor.
    altered = stream.clone()
    altered[:, :, 48] = 1.0 - altered[:, :, 48]
    a_energy, _ = run(Main, stream=stream)
    b_energy, _ = run(Main, stream=altered)

    # The no-interoception interface has 48 RGB sensors; compare it with the
    # same RGB stream presented to a 49-sensor brain at neutral energy.
    rgb = stream[:, :, :48]
    no_i, bni = run(Main, sensors=48, stream=rgb)
    neutral = stream.clone()
    neutral[:, :, 48] = 0.5
    neutral_i, _ = run(Main, stream=neutral)

    def rmse(a, b):
        return float((a - b).square().mean().sqrt())

    def maxabs(a, b):
        return float((a - b).abs().max())

    out = {
        "source_sha256": {"main": sha(main_path), "control": sha(ctl_path)},
        "row_173_recorded_main_sha256": "4a55e99d484ad0085394e5d087ecdd0606c2b248bc96aab725d6e8d55dd1c300",
        "main_vs_control": {
            "action_rmse": rmse(nominal, control),
            "action_max_abs": maxabs(nominal, control),
            "control_matches_main_package_params": {"action_rmse": rmse(control, package), "action_max_abs": maxabs(control, package)},
        },
        "component_probes": {
            "energy_coupling_zero_rmse": rmse(nominal, no_coupling),
            "readiness_recovery_zero_rmse": rmse(nominal, no_recovery),
            "readiness_cost_zero_rmse": rmse(nominal, no_cost),
            "bright_readiness_recovery_zero_rmse": rmse(bright_main, bright_no_recovery),
            "bright_readiness_cost_zero_rmse": rmse(bright_main, bright_no_cost),
            "bright_bites_main": float(bright_main[:, :, 2].sum()),
            "bright_bites_no_recovery": float(bright_no_recovery[:, :, 2].sum()),
            "bright_bites_no_cost": float(bright_no_cost[:, :, 2].sum()),
            "bright_readiness_final_main": float(bbm.readiness.mean()),
            "bright_readiness_final_no_recovery": float(bbr.readiness.mean()),
        },
        "energy_input": {
            "last_sensor_flip_rmse": rmse(a_energy, b_energy),
            "last_sensor_flip_max_abs": maxabs(a_energy, b_energy),
            "no_interoception_vs_neutral_rmse": rmse(no_i, neutral_i),
            "no_interoception_readiness_final": float(bni.readiness.mean()),
            "neutral_readiness_final": float(run(Main, stream=neutral)[1].readiness.mean()),
        },
        "scaling": {
            "action_rmse_302_vs_100000": rmse(nominal, large),
            "units_302": float(bm.structure()["units"]),
            "units_100000": float(bl.structure()["units"]),
            "connections_302": float(bm.structure()["connections"]),
            "connections_100000": float(bl.structure()["connections"]),
        },
        "source_flags": {
            "fixed_eye_context_slice": "eye[:, 4:]" in main_path.read_text(),
            "fixed_thresholds": ["> 0.04", "> 0.42", "> 0.24", "> 0.5"],
            "age_or_periodic_gate": "age" in main_path.read_text(),
            "allocates_n_units_state": "n_units" in main_path.read_text(),
        },
    }
    result = ROOT / "audit/metabolic_gate_entry_audit.result.json"
    result.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
