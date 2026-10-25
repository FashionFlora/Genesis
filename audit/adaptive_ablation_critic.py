"""Protocol-aligned critic probe for adaptive-retention candidate and ablation."""

import importlib.util
import json
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.OrganismBrain


def run(cls, stream, seed=31, previous_energy=None):
    brain = cls(302, stream.shape[-1], 3, stream.shape[1], "cpu", seed=seed)
    if previous_energy is not None:
        brain.previous_energy.fill_(previous_energy)
    actions = torch.stack([brain.act(frame).detach() for frame in stream])
    return actions, brain


def rmse(a, b):
    return float((a - b).square().mean().sqrt())


def bright(energies, batch=16):
    stream = torch.zeros(len(energies), batch, 49)
    stream[:, :, 24] = 1.0
    stream[:, :, 48] = torch.as_tensor(energies, dtype=torch.float32)[:, None]
    return stream


def bite_ages(actions):
    return [int(i) for i in torch.where(actions[:, 0, 2] > 0)[0]]


def main():
    main_cls = load(ROOT / "candidates/life_metabolic_adaptive_retention_budget/principle_organism.py", "main")
    control_cls = load(ROOT / "candidates/life_metabolic_adaptive_retention_budget_ablation/principle_organism.py", "control")

    constant_095 = bright([0.95] * 32)
    constant_050 = bright([0.50] * 32)
    step = bright([0.95] * 8 + [0.50] * 24)
    no_energy = constant_095[:, :, :48]

    m095, bm095 = run(main_cls, constant_095)
    c095, bc095 = run(control_cls, constant_095)
    # Align the internal prior to the stream to distinguish startup mismatch.
    m050a, bm050a = run(main_cls, constant_050, previous_energy=0.50)
    c050a, bc050a = run(control_cls, constant_050, previous_energy=0.50)
    # The default prior intentionally matches the judge's initial energy.
    m050, bm050 = run(main_cls, constant_050)
    c050, bc050 = run(control_cls, constant_050)
    ms, bs = run(main_cls, step)
    cs, bcs = run(control_cls, step)
    mn, bmn = run(main_cls, no_energy)
    cn, bcn = run(control_cls, no_energy)

    out = {
        "constant_energy_095": {
            "action_rmse": rmse(m095, c095),
            "main_bite_ages": bite_ages(m095),
            "control_bite_ages": bite_ages(c095),
            "main_preference_max": float(bm095.preference.abs().max()),
            "control_preference_max": float(bc095.preference.abs().max()),
        },
        "constant_energy_050_aligned_prior": {
            "action_rmse": rmse(m050a, c050a),
            "main_bite_ages": bite_ages(m050a),
            "control_bite_ages": bite_ages(c050a),
            "main_preference_max": float(bm050a.preference.abs().max()),
        },
        "constant_energy_050_default_prior": {
            "action_rmse": rmse(m050, c050),
            "main_bite_ages": bite_ages(m050),
            "control_bite_ages": bite_ages(c050),
            "main_preference_max": float(bm050.preference.abs().max()),
        },
        "energy_step_095_to_050": {
            "action_rmse": rmse(ms, cs),
            "pre_step_rmse": rmse(ms[:8], cs[:8]),
            "post_step_rmse": rmse(ms[8:], cs[8:]),
            "main_preference_max": float(bs.preference.abs().max()),
        },
        "no_energy_sensor": {
            "action_rmse": rmse(mn, cn),
            "main_preference_max": float(bmn.preference.abs().max()),
        },
        "source_flags": {
            "fixed_eye_slice": "eye[:, 4:]" in (ROOT / "candidates/life_metabolic_adaptive_retention_budget/principle_organism.py").read_text(),
            "green_parity_context": "0::2" in (ROOT / "candidates/life_metabolic_adaptive_retention_budget/principle_organism.py").read_text(),
            "periodic_age_gate": "remainder(5)" in (ROOT / "candidates/life_metabolic_adaptive_retention_budget/principle_organism.py").read_text(),
        },
    }
    path = ROOT / "audit/adaptive_ablation_critic.result.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
