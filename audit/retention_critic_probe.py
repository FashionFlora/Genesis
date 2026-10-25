"""Behavior/source audit for dynamics_metabolic_retention.

This is a small deterministic probe, not a substitute for the full judge.
It isolates sensor dependence and the claimed reserve-coupled trace.
"""
import importlib.util
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "retention_probe", ROOT / "candidates/dynamics_metabolic_retention/principle_organism.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def run(sensors, params=None, n_units=302):
    brain = mod.OrganismBrain(n_units, sensors.shape[-1], 3, sensors.shape[1], "cpu", params=params)
    actions = []
    for frame in sensors:
        actions.append(brain.act(frame).detach().clone())
    return torch.stack(actions), brain


def rmse(a, b):
    return float((a - b).square().mean().sqrt())


def main():
    torch.manual_seed(251025)
    steps, batch = 96, 32
    base = torch.rand(steps, batch, 49)
    base[:, :, -1] = torch.linspace(0.1, 0.9, steps)[:, None]

    first_pixels = base.clone()
    first_pixels[:, :, :12] = torch.rand_like(first_pixels[:, :, :12])
    suffix_pixels = base.clone()
    suffix_pixels[:, :, 12:24] = torch.rand_like(suffix_pixels[:, :, 12:24])

    # Swap complete RGB columns in the color channels while leaving energy fixed.
    permuted = base[:, :, :48].clone().reshape(steps, batch, 16, 3)
    permuted[:, :, :, [0, 1]] = permuted[:, :, :, [1, 0]]
    permuted = torch.cat((permuted.reshape(steps, batch, 48), base[:, :, -1:]), dim=2)

    no_intero = base[:, :, :48]
    neutral = base.clone()
    neutral[:, :, -1] = 0.5

    y, brain = run(base)
    yi, _ = run(first_pixels)
    ys, _ = run(suffix_pixels)
    yp, _ = run(permuted)
    yn, _ = run(neutral)
    y0, b0 = run(no_intero)

    bright = torch.zeros(240, 1, 49)
    bright[:, :, 12:15] = 0.9
    bright[:, :, -1] = 0.8
    yb, bm = run(bright)
    ys0, bslow = run(bright, {"energy_coupling": 0.0})
    yf, bfast = run(bright, {"trace_forgetting": 0.20})

    result = {
        "stream": {"batch": batch, "steps": steps, "seed": 251025},
        "sensor_dependence": {
            "first_4_pixels_action_rmse": rmse(y, yi),
            "suffix_pixels_action_rmse": rmse(y, ys),
            "swap_r_g_action_rmse": rmse(y, yp),
            "48_sensor_vs_neutral_49_action_rmse": rmse(y0, yn),
            "no_intero_final_preference_abs_sum": float(b0.preference.abs().sum()),
        },
        "trace_isolation": {
            "nominal_final_eligibility_mean": float(bm.eligibility.mean()),
            "coupling_zero_final_eligibility_mean": float(bslow.eligibility.mean()),
            "forgetting_020_final_eligibility_mean": float(bfast.eligibility.mean()),
            "nominal_bites": float(yb[:, :, 2].sum()),
            "coupling_zero_bites": float(ys0[:, :, 2].sum()),
            "forgetting_020_bites": float(yf[:, :, 2].sum()),
            "nominal_vs_coupling_zero_action_rmse": rmse(yb, ys0),
            "nominal_vs_forgetting_020_action_rmse": rmse(yb, yf),
        },
        "structure": {
            "n_units_302": brain.structure(),
            "n_units_100000": run(base, n_units=100000)[1].structure(),
        },
        "source_flags": {
            "fixed_eye_slice": "eye[:, 4:]",
            "fixed_thresholds": [">0.04", ">0.42", ">0.24", ">0.5"],
            "fixed_three_color_state": True,
        },
    }
    out = ROOT / "audit/retention_critic_probe.result.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
