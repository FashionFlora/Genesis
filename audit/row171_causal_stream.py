"""Causal stream and invariance audit for leaderboard row 171."""
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.OrganismBrain


def rollout(cls, frames, n_units=302, seed=23):
    brain = cls(n_units, frames.shape[-1], 3, frames.shape[1], "cpu", seed=seed)
    actions = []
    for frame in frames:
        actions.append(brain.act(frame).detach().numpy())
    return np.stack(actions), brain


def main():
    source = ROOT / "candidates/axiom_metabolic_retention_budget/principle_organism.py"
    control = ROOT / "candidates/axiom_metabolic_retention_budget_ablation/principle_organism.py"
    Cand = load(source, "row171_candidate")
    # Keep the candidate module isolated: the control imports and patches its parent.
    Abl = load(control, "row171_control")
    rng = np.random.default_rng(171)
    rgb = rng.random((96, 12, 48), dtype=np.float32)
    energy = rng.random((96, 12, 1), dtype=np.float32)
    frames = np.concatenate([rgb, energy], axis=-1)
    cand, bc = rollout(Cand, frames)
    abl, ba = rollout(Abl, frames)
    no_energy = frames[..., :48]
    no_e_cand, _ = rollout(Cand, no_energy)
    small, _ = rollout(Cand, frames, 302)
    large, _ = rollout(Cand, frames, 100000)
    # A channel permutation should change a genuinely retinally grounded policy,
    # while a pure n_units capacity claim should change the state or actions.
    perm = frames.copy()
    perm[..., :48] = perm[..., :48].reshape(96, 12, 16, 3)[..., ::-1, :].reshape(96, 12, 48)
    perm_actions, _ = rollout(Cand, perm)
    text = source.read_text().lower()
    result = {
        "candidate_vs_fixed_retention_action_rmse": float(np.sqrt(np.mean((cand - abl) ** 2))),
        "candidate_vs_fixed_retention_action_max": float(np.max(np.abs(cand - abl))),
        "state_preference_max_delta": float(np.max(np.abs(bc.preference.detach().numpy() - ba.preference.detach().numpy()))),
        "energy_omitted_action_rmse": float(np.sqrt(np.mean((cand - no_e_cand) ** 2))),
        "n_units_302_vs_100000_action_rmse": float(np.sqrt(np.mean((small - large) ** 2))),
        "retinal_sector_reverse_action_rmse": float(np.sqrt(np.mean((cand - perm_actions) ** 2))),
        "structure_302": bc.structure(),
        "structure_100000": rollout(Cand, frames, 100000)[1].structure(),
        "hardcoded_tokens": {t: (t in text) for t in ("eye[:, 4:]", "remainder(5)", "3, 2", "green", "math.pi")},
    }
    out = ROOT / "audit/row171_causal_stream.result.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
