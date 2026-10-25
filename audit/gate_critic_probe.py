"""Small source/behavior audit for dynamics_metabolic_gate.

The probe is intentionally separate from the organism judge: it tests whether
the claimed readiness mechanism is distinguishable from fixed retinal rules.
"""
import importlib.util
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


main = load(ROOT / "candidates/dynamics_metabolic_gate/principle_organism.py", "gate_main_probe")


def run(sensors, params=None):
    if sensors.ndim == 2:
        sensors = sensors[:, None, :]
    brain = main.OrganismBrain(302, sensors.shape[2], 3, sensors.shape[1], "cpu", params=params)
    out = []
    readiness = []
    for row in sensors:
        out.append(brain.act(row).detach().clone())
        readiness.append(brain.readiness.detach().clone())
    return torch.cat(out, dim=0), torch.cat(readiness, dim=0)


def main_probe():
    torch.manual_seed(12025)
    b, t = 32, 80
    x = torch.rand(t, b, 49)
    x[:, :, -1] = torch.linspace(0.1, 0.9, t)[:, None]
    base = x
    # `eye[:, 4:]` means the first four RGB pixels are ignored by all choices.
    ignored = base.clone()
    ignored[:, :, :12] = torch.rand_like(ignored[:, :, :12])
    used = base.clone()
    used[:, :, 12:24] = torch.rand_like(used[:, :, 12:24])
    # Swap two complete RGB sectors in the used suffix.
    swapped = base.clone()
    a, z = swapped[:, :, 12:15].clone(), swapped[:, :, 15:18].clone()
    swapped[:, :, 12:15], swapped[:, :, 15:18] = z, a

    y, r = run(base)
    yi, _ = run(ignored)
    yu, _ = run(used)
    ys, _ = run(swapped)
    no_energy, r_no = run(base[:, :, :48])
    neutral = base.clone(); neutral[:, :, -1] = 0.5
    yn, r_neutral = run(neutral)

    bright = torch.zeros(240, 1, 49)
    bright[:, :, 12:15] = 0.9
    bright[:, :, -1] = 0.8
    _, r_main = run(bright)
    _, r_no_recovery = run(bright, {"readiness_recovery": 0.0})
    _, r_no_cost = run(bright, {"readiness_cost": 0.0})
    _, r_no_coupling = run(bright, {"energy_coupling": 0.0})

    def rmse(a, b):
        return float((a - b).square().mean().sqrt())

    result = {
        "stream": {"batch": b, "steps": t, "seed": 12025},
        "retinal_confound": {
            "first_4_pixels_motor_action_rmse": rmse(y, yi),
            "used_pixel_action_rmse": rmse(y, yu),
            "swap_used_sectors_action_rmse": rmse(y, ys),
        },
        "interoception": {
            "48_sensor_vs_neutral_49_action_rmse": rmse(no_energy, yn),
            "48_sensor_final_readiness": float(r_no[-1].mean()),
            "neutral_49_final_readiness": float(r_neutral[-1].mean()),
        },
        "component_isolation": {
            "main_bites": float(run(bright)[0][:, 2].sum()),
            "no_recovery_bites": float(run(bright, {"readiness_recovery": 0.0})[0][:, 2].sum()),
            "no_cost_bites": float(run(bright, {"readiness_cost": 0.0})[0][:, 2].sum()),
            "no_coupling_bites": float(run(bright, {"energy_coupling": 0.0})[0][:, 2].sum()),
            "main_final_readiness": float(r_main[-1].mean()),
            "no_recovery_final_readiness": float(r_no_recovery[-1].mean()),
            "no_cost_final_readiness": float(r_no_cost[-1].mean()),
            "no_coupling_final_readiness": float(r_no_coupling[-1].mean()),
        },
        "source_flags": {
            "fixed_eye_slice": True,
            "fixed_thresholds": [">0.04", ">0.42", ">0.24", ">0.5"],
            "allocates_n_units": False,
        },
    }
    out = ROOT / "audit/gate_critic_probe.result.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main_probe()
