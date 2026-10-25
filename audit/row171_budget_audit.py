"""Counterfactual audit for axiom_metabolic_retention_budget (row 171)."""
import importlib.util
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem + str(path.parent), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.OrganismBrain


def run(cls, n_units, frames, seed=11):
    brain = cls(n_units, 49, 3, len(frames[0]), "cpu", seed=seed)
    out = []
    for frame in frames:
        out.append(brain.act(frame).detach().numpy())
    return np.stack(out), brain


def scene(batch=8, energy=0.5, color=0, green_parity=0, bright=True):
    x = np.zeros((batch, 49), dtype=np.float32)
    # The final sensor is the optional interoceptive channel for 48 RGB inputs.
    x[:, 48] = energy
    if bright:
        # One bright source in sector 8; leave the first four sectors empty so
        # the candidate's eye[:, 4:] shortcut is observable.
        x[:, (8 * 3) + color] = 0.8
    # The context bit is decoded from green values at even/odd sectors.
    if green_parity:
        x[:, 1::6] = 0.01
    else:
        x[:, 4::6] = 0.01
    return x


def main():
    cand_path = ROOT / "candidates/axiom_metabolic_retention_budget/principle_organism.py"
    abl_path = ROOT / "candidates/axiom_metabolic_retention_budget_ablation/principle_organism.py"
    # The ablation module monkey-patches the class it imports. Load and run
    # the candidate before importing the ablation, otherwise both aliases
    # silently become the control.
    Cand = load(cand_path)
    frames = [scene(energy=0.5, color=0, green_parity=0) for _ in range(12)]
    frames[0] = scene(energy=0.95, color=0, green_parity=0)
    frames[1] = scene(energy=0.20, color=1, green_parity=1)
    frames[2:] = [scene(energy=0.20, color=1, green_parity=1) for _ in frames[2:]]
    c302, bc = run(Cand, 302, frames)
    c100k, _ = run(Cand, 100000, frames)
    # Color and green-parity permutations isolate the hard-coded context path.
    color_swap = [scene(energy=0.5, color=2, green_parity=0) for _ in range(12)]
    parity_swap = [scene(energy=0.5, color=0, green_parity=1) for _ in range(12)]
    cs, _ = run(Cand, 302, color_swap)
    ps, _ = run(Cand, 302, parity_swap)
    pulse_frames = [scene(energy=0.5, color=0, green_parity=0) for _ in range(12)]
    pulse, _ = run(Cand, 302, pulse_frames)
    learn_frames = [scene(energy=(0.2 if i % 2 else 0.8), color=i % 2, green_parity=i % 2)
                    for i in range(24)]
    learned, blc = run(Cand, 302, learn_frames)
    Abl = load(abl_path)
    a302, ba = run(Abl, 302, frames)
    learned_abl, bla = run(Abl, 302, learn_frames)
    result = {
        "n_units_max_abs_delta": float(np.max(np.abs(c302 - c100k))),
        "ablation_max_abs_delta": float(np.max(np.abs(c302 - a302))),
        "color_swap_mean_abs_delta": float(np.mean(np.abs(c302 - cs))),
        "green_parity_swap_mean_abs_delta": float(np.mean(np.abs(c302 - ps))),
        "bite_ages": np.flatnonzero(pulse[:, 0, 2] > 0.5).tolist(),
        "bite_matrix": pulse[:, :, 2].astype(int).tolist(),
        "preference_state_candidate_vs_ablation": float(
            np.max(np.abs(blc.preference.detach().numpy() - bla.preference.detach().numpy()))
        ),
        "learning_action_max_abs_delta": float(np.max(np.abs(learned - learned_abl))),
        "candidate_actions_first": c302[:6, 0].round(6).tolist(),
        "ablation_actions_first": a302[:6, 0].round(6).tolist(),
        "structure": bc.structure(),
        "class_modules": [Cand.__module__, Abl.__module__],
        "same_class": bool(Cand is Abl),
        "preference_max": [float(blc.preference.abs().max()), float(bla.preference.abs().max())],
        "eligibility_max": [float(blc.eligibility.max()), float(bla.eligibility.max())],
        "init_names": [Cand.__init__.__name__, Abl.__init__.__name__],
    }
    out = ROOT / "audit/row171_budget_audit.result.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
