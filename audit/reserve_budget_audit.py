"""Audit the newest reserve-budget candidate for causal leakage.

This is a smoke/provenance probe, not an organism judge.  It keeps the
candidate and its matched control in separate module namespaces and reports
only deterministic quantities that can be reproduced from the source.
"""

import importlib.util
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]


def load(path, tag):
    spec = importlib.util.spec_from_file_location(tag, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def brain(module, sensors=49, batch=4, units=302, seed=11):
    return module.OrganismBrain(units, sensors, 3, batch, "cpu", seed=seed)


def rollout(module, frames, units=302, seed=11):
    b = brain(module, frames.shape[-1], frames.shape[1], units, seed)
    out = []
    for frame in frames:
        out.append(b.act(frame).detach().clone())
    return torch.stack(out), b.structure()


def scene(steps=20, batch=4, energy=None, source=8):
    x = torch.zeros(steps, batch, 49)
    x[:, :, source * 3 + 1] = 1.0
    if energy is None:
        x[:, :, 48] = 0.5
    elif energy.ndim == 1:
        x[:, :, 48] = energy[:, None]
    else:
        x[:, :, 48] = energy
    return x


def main():
    main_mod = load("candidates/dynamics_metabolic_reserve_budget/principle_organism.py", "reserve_main")
    ctrl_mod = load("candidates/dynamics_metabolic_reserve_budget_ablation/principle_organism.py", "reserve_ctrl")

    constant = scene(steps=40)
    blank = torch.zeros(40, 4, 49)
    blank[:, :, 48] = 0.5
    source0 = scene(steps=40, source=0)
    boundary = scene(steps=40, source=4)
    alternating = scene(steps=40, energy=(torch.arange(40) % 2).float())
    generator = torch.Generator().manual_seed(23)
    random_frames = torch.rand(80, 4, 49, generator=generator)
    no_energy = torch.zeros(40, 4, 48)
    no_energy[:, :, 8 * 3 + 1] = 1.0

    a_const, s_main = rollout(main_mod, constant)
    a_blank, _ = rollout(main_mod, blank)
    a_source0, _ = rollout(main_mod, source0)
    a_boundary, _ = rollout(main_mod, boundary)
    c_const, s_ctrl = rollout(ctrl_mod, constant)
    a_alt, _ = rollout(main_mod, alternating)
    c_alt, _ = rollout(ctrl_mod, alternating)
    a_random, _ = rollout(main_mod, random_frames)
    c_random, _ = rollout(ctrl_mod, random_frames)
    a_no, _ = rollout(main_mod, no_energy)
    a_big, s_big = rollout(main_mod, constant, units=100000)

    result = {
        "main_structure_302": s_main,
        "main_structure_100000": s_big,
        "control_structure_302": s_ctrl,
        "constant_main_vs_control_max_action_delta": float((a_const - c_const).abs().max()),
        "alternating_main_vs_control_max_action_delta": float((a_alt - c_alt).abs().max()),
        "random_main_vs_control_max_action_delta": float((a_random - c_random).abs().max()),
        "random_main_vs_control_action_rmse": float((a_random - c_random).square().mean().sqrt()),
        "alternating_main_vs_constant_max_action_delta": float((a_alt - a_const).abs().max()),
        "energy_omitted_vs_neutral_max_action_delta": float((a_no - a_const).abs().max()),
        "pixel0_vs_blank_max_action_delta": float((a_source0 - a_blank).abs().max()),
        "pixel0_vs_pixel8_max_action_delta": float((a_source0 - a_const).abs().max()),
        "included_pixel4_vs_pixel8_max_action_delta": float((a_boundary - a_const).abs().max()),
        "units_302_vs_100000_max_action_delta": float((a_const - a_big).abs().max()),
        "constant_bite_ages": a_const[:, 0, 2].nonzero().flatten().tolist(),
        "constant_bite_count": int(a_const[:, :, 2].sum()),
        "control_constant_bite_ages": c_const[:, 0, 2].nonzero().flatten().tolist(),
        "control_constant_bite_count": int(c_const[:, :, 2].sum()),
    }
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    (ROOT / "audit/reserve_budget_audit.result.json").write_text(text + "\n")


if __name__ == "__main__":
    main()
